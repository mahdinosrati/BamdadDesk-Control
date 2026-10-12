import base64
import hashlib
import json
import os
import re
import secrets
import time
import uuid
from pathlib import Path

from argon2.exceptions import VerificationError
from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from .catalog import PERMISSIONS, catalog, validate_options
from .body_limit import BodyLimit
from .storage import PASSWORDS, Store, canonical, digest
from .scopes import device_in_scope, group_allowed, policy_in_scope, require_global, require_group, set_scope
from .reporting import router as reporting_router
from .administration import router as administration_router
from .reports import router as reports_router
from .organization import router as organization_router, settings as organization_settings


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Login(Model):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)


class AdminInput(Login):
    permissions: list[str]
    groups: list[str] | None = None


class AdminEdit(Model):
    permissions: list[str]
    active: bool
    password: str | None = Field(default=None, min_length=12, max_length=256)
    groups: list[str] | None = None


class GroupInput(Model):
    name: str = Field(min_length=1, max_length=100)


class DeviceEdit(Model):
    group_id: str = Field(default="", max_length=40)
    active: bool = True
    alias: str | None = Field(default=None, max_length=100)
    note: str | None = Field(default=None, max_length=2000)


class EnrollmentInput(Model):
    label: str = Field(min_length=1, max_length=100)
    group_id: str = Field(default="", max_length=40)
    hours: int = Field(default=24, ge=1, le=168)
    uses: int = Field(default=1, ge=1, le=1000)


class Enroll(Model):
    token: str = Field(min_length=20, max_length=200)
    name: str = Field(min_length=1, max_length=100)
    version: str = Field(min_length=1, max_length=40)
    rustdesk_id: str = Field(default="", max_length=50)


class Heartbeat(Model):
    name: str = Field(min_length=1, max_length=100)
    version: str = Field(min_length=1, max_length=40)
    rustdesk_id: str = Field(default="", max_length=50)
    applied: int = Field(default=0, ge=0)
    error: str = Field(default="", max_length=200)
    platform: str = Field(default='', max_length=100)
    username: str = Field(default='', max_length=100)


class PolicyInput(Model):
    options: dict[str, str]
    password: str | None = Field(default=None, min_length=1, max_length=128)
    clear_password_override: bool = False
    expected_revision: int = Field(ge=1)


def create_app(directory=None, secure=None):
    app = FastAPI(title="BamdadDesk Control", docs_url=None, redoc_url=None)
    app.add_middleware(BodyLimit)
    store = Store(directory or os.environ.get("BAMDAD_DATA", "./data"))
    app.state.store = store
    secure = secure if secure is not None else not (
        os.environ.get("BAMDAD_DEV_HTTP") == "1" or os.environ.get("BAMDAD_ALLOW_HTTP") == "1"
    )
    static = Path(__file__).parent.parent / "static"

    @app.middleware("http")
    async def security_headers(request, call_next):
        if request.url.path == "/api/releases" and request.method == "POST":
            try:
                admin = current_admin(request)
                if "releases.write" not in json.loads(admin["permissions"]):
                    raise HTTPException(403, "Permission denied")
                require_global(admin)
            except HTTPException as exc:
                return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            length = request.headers.get("content-length", "0")
            try:
                maximum = 200 * 1024 * 1024 if request.url.path == "/api/releases" else 64 * 1024
                if int(length) > maximum:
                    return JSONResponse({"detail": "Request too large"}, status_code=413)
            except ValueError:
                return JSONResponse({"detail": "Invalid length"}, status_code=400)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    def same_origin(request):
        origin = request.headers.get("origin")
        expected = os.environ.get("BAMDAD_ORIGIN", str(request.base_url).rstrip("/"))
        if origin and origin != expected:
            raise HTTPException(403, "Origin rejected")

    def current_admin(request: Request):
        token = request.cookies.get("bamdad_session", "")
        with store.connect() as db:
            row = db.execute("SELECT a.*,s.csrf FROM admins a JOIN sessions s ON a.id=s.admin "
                             "WHERE s.token=? AND s.expires>? AND a.active=1", (digest(token), int(time.time()))).fetchone()
        if row is None:
            raise HTTPException(401, "Sign in required")
        with store.connect() as db:
            scope = db.execute('SELECT groups_json FROM admin_scopes WHERE admin=?', (row['id'],)).fetchone()
        row = {**dict(row), 'groups': json.loads(scope[0]) if scope else None}
        if request.method not in ("GET", "HEAD"):
            same_origin(request)
            if not secrets.compare_digest(request.headers.get("x-csrf-token", ""), row["csrf"]):
                raise HTTPException(403, "CSRF token required")
        return dict(row)

    def require(permission):
        def check(admin=Depends(current_admin)):
            if permission not in json.loads(admin["permissions"]):
                raise HTTPException(403, "Permission denied")
            if permission in ('admins.write', 'releases.write'):
                require_global(admin)
            return admin
        return check

    def device_auth(request: Request):
        scheme, _, token = request.headers.get("authorization", "").partition(" ")
        if scheme != "Bearer" or not token:
            raise HTTPException(401, "Device token required")
        with store.connect() as db:
            row = db.execute("SELECT * FROM devices WHERE token=? AND active=1", (digest(token),)).fetchone()
        if not row:
            raise HTTPException(401, "Device not enrolled or disabled")
        return dict(row)

    def group_exists(db, group_id):
        if group_id and not db.execute("SELECT 1 FROM groups WHERE id=?", (group_id,)).fetchone():
            raise HTTPException(404, "Group not found")

    def validate_permissions(values):
        if not set(values) <= set(PERMISSIONS) or len(values) != len(set(values)):
            raise HTTPException(422, "Invalid permissions")

    def effective_policy(db, device):
        options = {"verification-method": "use-both-passwords", "access-mode": "custom"}
        password = None
        scopes = ["global"]
        if device["group_id"]:
            scopes.append("group:" + device["group_id"])
        scopes.append("device:" + device["id"])
        for scope in scopes:
            row = db.execute("SELECT * FROM policies WHERE scope=?", (scope,)).fetchone()
            if row:
                options.update(json.loads(row["options"]))
                if row["password"] is not None:
                    password = json.loads(row["password"])
        revision = db.execute("SELECT value FROM meta WHERE key='revision'").fetchone()[0]
        return {"schema": 1, "device_id": device["id"], "revision": revision,
                "options": options, "password": password}

    @app.get("/healthz")
    def health():
        return {"status": "ok"}

    @app.post("/api/login")
    def login(body: Login, request: Request):
        same_origin(request)
        address = request.client.host if request.client else "unknown"
        now = int(time.time())
        with store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("DELETE FROM login_attempts WHERE started<?", (now - 900,))
            attempt = db.execute("SELECT count FROM login_attempts WHERE address=?", (address,)).fetchone()
            if attempt and attempt[0] >= 10:
                raise HTTPException(429, "Too many attempts; try again in 15 minutes")
            db.execute("INSERT INTO login_attempts VALUES (?,1,?) ON CONFLICT(address) DO UPDATE SET count=count+1", (address, now))
        with store.connect() as db:
            row = db.execute("SELECT * FROM admins WHERE username=? AND active=1", (body.username,)).fetchone()
            valid = False
            if row:
                try:
                    valid = PASSWORDS.verify(row["password"], body.password)
                except VerificationError:
                    pass
            if not valid:
                raise HTTPException(401, "Incorrect username or password")
            token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
            db.execute("DELETE FROM login_attempts WHERE address=?", (address,))
            db.execute("DELETE FROM sessions WHERE expires<?", (now,))
            db.execute("INSERT INTO sessions VALUES (?,?,?,?)", (digest(token), row["id"], csrf, now + 8 * 3600))
            store.audit(db, row["username"], "login", row["id"])
        response = JSONResponse({"csrf": csrf})
        response.set_cookie("bamdad_session", token, max_age=8 * 3600, httponly=True, secure=secure, samesite="strict")
        return response

    @app.get("/api/me")
    def me(admin=Depends(current_admin)):
        return {"id": admin["id"], "username": admin["username"], "permissions": json.loads(admin["permissions"]), "csrf": admin["csrf"], 'groups': admin['groups']}

    @app.post("/api/logout")
    def logout(request: Request, admin=Depends(current_admin)):
        with store.connect() as db:
            db.execute("DELETE FROM sessions WHERE token=?", (digest(request.cookies.get("bamdad_session", "")),))
        response = JSONResponse({"ok": True})
        response.delete_cookie("bamdad_session")
        return response

    @app.get("/api/catalog")
    def policy_catalog(admin=Depends(current_admin)):
        return {"options": catalog(), "permissions": PERMISSIONS, "public_key": store.public_key()}

    @app.get("/api/devices")
    def devices(admin=Depends(require("devices.read"))):
        with store.connect() as db:
            rows = db.execute("SELECT id,name,group_id,rustdesk_id,version,last_seen,applied,error,active FROM devices ORDER BY name").fetchall()
            revision = db.execute("SELECT value FROM meta WHERE key='revision'").fetchone()[0]
        return {"revision": revision, "devices": [dict(row) for row in rows if group_allowed(admin, row['group_id'])]}

    @app.put("/api/devices/{device_id}")
    def edit_device(device_id: str, body: DeviceEdit, admin=Depends(require("devices.write"))):
        with store.connect() as db:
            old = device_in_scope(db, admin, device_id)
            require_group(admin, body.group_id)
            group_exists(db, body.group_id)
            result = db.execute("UPDATE devices SET group_id=?,active=? WHERE id=?", (body.group_id, body.active, device_id))
            if result.rowcount == 0:
                raise HTTPException(404, "Device not found")
            store.bump(db)
            db.execute('INSERT OR IGNORE INTO device_details(device) VALUES (?)', (device_id,))
            if body.alias is not None:
                db.execute('UPDATE device_details SET alias=? WHERE device=?', (body.alias, device_id))
            if body.note is not None:
                db.execute('UPDATE device_details SET note=? WHERE device=?', (body.note, device_id))
            store.audit(db, admin["username"], "device.update", device_id, old['group_id'])
        return {"ok": True}

    @app.get("/api/groups")
    def groups(admin=Depends(require("devices.read"))):
        with store.connect() as db:
            return [dict(r) for r in db.execute("SELECT * FROM groups ORDER BY name") if group_allowed(admin, r['id'])]

    @app.post("/api/groups")
    def add_group(body: GroupInput, admin=Depends(require("devices.write"))):
        require_global(admin)
        identifier = str(uuid.uuid4())
        with store.connect() as db:
            if db.execute("SELECT 1 FROM groups WHERE name=?", (body.name,)).fetchone():
                raise HTTPException(409, "Group already exists")
            db.execute("INSERT INTO groups VALUES (?,?)", (identifier, body.name))
            store.audit(db, admin["username"], "group.create", identifier)
        return {"id": identifier}

    @app.post("/api/enrollments")
    def enrollment(body: EnrollmentInput, admin=Depends(require("enrollment.write"))):
        token = secrets.token_urlsafe(32)
        expires = int(time.time()) + body.hours * 3600
        with store.connect() as db:
            group_exists(db, body.group_id)
            require_group(admin, body.group_id)
            db.execute("INSERT INTO enrollments VALUES (?,?,?,?,?)", (digest(token), body.label, body.group_id, expires, body.uses))
            db.execute('INSERT INTO enrollment_details(token,id,created,used) VALUES (?,?,?,0)', (digest(token), str(uuid.uuid4()), int(time.time())))
            store.audit(db, admin["username"], "enrollment.create", body.label, body.group_id)
        return {"token": token, "expires": expires, "public_key": store.public_key()}

    @app.post("/api/agent/enroll")
    def enroll(body: Enroll):
        now, identifier, token = int(time.time()), str(uuid.uuid4()), secrets.token_urlsafe(32)
        with store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM enrollments WHERE token=? AND expires>? AND remaining>0", (digest(body.token), now)).fetchone()
            if not row:
                raise HTTPException(401, "Enrollment expired or invalid")
            if db.execute('SELECT 1 FROM automatic_enrollments WHERE token=?', (digest(body.token),)).fetchone() and not organization_settings(db)['automatic_enrollment']:
                raise HTTPException(403, 'Automatic enrollment is currently disabled')
            db.execute("UPDATE enrollments SET remaining=remaining-1 WHERE token=?", (digest(body.token),))
            db.execute('UPDATE enrollment_details SET used=used+1 WHERE token=?', (digest(body.token),))
            db.execute("INSERT INTO devices(id,token,name,group_id,version,rustdesk_id) VALUES (?,?,?,?,?,?)",
                       (identifier, digest(token), body.name, row["group_id"], body.version, body.rustdesk_id))
            store.audit(db, "device", "device.enroll", identifier, row['group_id'])
        return {"device_id": identifier, "token": token, "public_key": store.public_key()}

    @app.post("/api/agent/heartbeat")
    def heartbeat(body: Heartbeat, device=Depends(device_auth)):
        with store.connect() as db:
            policy = effective_policy(db, device)
            if body.applied > policy["revision"]:
                raise HTTPException(422, "Unknown policy revision")
            db.execute("UPDATE devices SET name=?,version=?,rustdesk_id=?,last_seen=?,applied=?,error=? WHERE id=?",
                       (body.name, body.version, body.rustdesk_id, int(time.time()), body.applied, body.error, device["id"]))
            db.execute('INSERT OR IGNORE INTO device_details(device) VALUES (?)', (device['id'],))
            db.execute('UPDATE device_details SET platform=?,username=? WHERE device=?', (body.platform, body.username, device['id']))
        return store.sign(policy)

    @app.get("/api/policies/{scope}")
    def get_policy(scope: str, admin=Depends(require("policies.write"))):
        with store.connect() as db:
            policy_in_scope(db, admin, scope)
            row = db.execute("SELECT * FROM policies WHERE scope=?", (scope,)).fetchone()
            revision = db.execute("SELECT value FROM meta WHERE key='revision'").fetchone()[0]
        return {"scope": scope, "options": json.loads(row["options"]) if row else {},
                "has_password": bool(row and row["password"]), "revision": revision}

    @app.put("/api/policies/{scope}")
    def put_policy(scope: str, body: PolicyInput, admin=Depends(require("policies.write"))):
        try:
            validate_options(body.options)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        if body.password is not None and body.clear_password_override:
            raise HTTPException(422, "Choose a password or inherit it")
        with store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            policy_group = policy_in_scope(db, admin, scope)
            kind, _, target = scope.partition(":")
            if scope != "global":
                table = {"group": "groups", "device": "devices"}.get(kind)
                if not table or not db.execute(f"SELECT 1 FROM {table} WHERE id=?", (target,)).fetchone():
                    raise HTTPException(404, "Policy scope not found")
            revision = db.execute("SELECT value FROM meta WHERE key='revision'").fetchone()[0]
            if body.expected_revision != revision:
                raise HTTPException(409, "Policy changed; reload before saving")
            old = db.execute("SELECT password FROM policies WHERE scope=?", (scope,)).fetchone()
            password = old[0] if old else None
            if body.clear_password_override:
                password = None
            if body.password is not None:
                salt = secrets.token_hex(16)
                storage = "00" + base64.b64encode(hashlib.sha256((body.password + salt).encode()).digest()).decode()
                password = canonical({"storage": storage, "salt": salt})
            revision = store.bump(db)
            db.execute("INSERT INTO policies VALUES (?,?,?,?) ON CONFLICT(scope) DO UPDATE SET options=excluded.options,password=excluded.password,revision=excluded.revision",
                       (scope, canonical(body.options), password, revision))
            store.audit(db, admin["username"], "policy.update", scope, policy_group)
        return {"revision": revision}

    @app.get("/api/admins")
    def admins(admin=Depends(require("admins.write"))):
        with store.connect() as db:
            scopes = {r['admin']: json.loads(r['groups_json']) for r in db.execute('SELECT * FROM admin_scopes')}
            return [{**dict(r), "permissions": json.loads(r["permissions"]), 'groups': scopes.get(r['id'])} for r in db.execute("SELECT id,username,permissions,active FROM admins ORDER BY username")]

    @app.post("/api/admins")
    def create_admin(body: AdminInput, admin=Depends(require("admins.write"))):
        validate_permissions(body.permissions)
        if len(body.password) < 12:
            raise HTTPException(422, "Admin password must be at least 12 characters")
        identifier = str(uuid.uuid4())
        with store.connect() as db:
            if db.execute("SELECT 1 FROM admins WHERE username=?", (body.username,)).fetchone():
                raise HTTPException(409, "Username already exists")
            db.execute("INSERT INTO admins(id,username,password,permissions) VALUES (?,?,?,?)",
                       (identifier, body.username, PASSWORDS.hash(body.password), canonical(body.permissions)))
            set_scope(db, identifier, body.groups, body.permissions)
            store.audit(db, admin["username"], "admin.create", identifier)
        return {"id": identifier}

    @app.put("/api/admins/{identifier}")
    def edit_admin(identifier: str, body: AdminEdit, admin=Depends(require("admins.write"))):
        validate_permissions(body.permissions)
        with store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM admins WHERE id=?", (identifier,)).fetchone()
            if not row:
                raise HTTPException(404, "Admin not found")
            previous_scope = db.execute('SELECT groups_json FROM admin_scopes WHERE admin=?', (identifier,)).fetchone()
            groups = body.groups if 'groups' in body.model_fields_set else (json.loads(previous_scope[0]) if previous_scope else None)
            remaining = [r for r in db.execute("SELECT id,permissions FROM admins WHERE active=1 AND id!=?", (identifier,))
                         if "admins.write" in json.loads(r["permissions"])]
            if (not body.active or "admins.write" not in body.permissions or groups is not None) and not remaining:
                raise HTTPException(409, "At least one active administrator must remain")
            password = PASSWORDS.hash(body.password) if body.password else row["password"]
            db.execute("UPDATE admins SET password=?,permissions=?,active=? WHERE id=?",
                       (password, canonical(body.permissions), body.active, identifier))
            set_scope(db, identifier, groups, body.permissions)
            db.execute("DELETE FROM sessions WHERE admin=?", (identifier,))
            store.audit(db, admin["username"], "admin.update", identifier)
        return {"ok": True}

    @app.get("/api/audit")
    def audit(before: int = 9223372036854775807, admin=Depends(require("audit.read"))):
        with store.connect() as db:
            if admin['groups'] is None:
                rows = db.execute('SELECT * FROM audit WHERE id<? ORDER BY id DESC LIMIT 200', (before,))
            else:
                marks = ','.join('?' for _ in admin['groups']) or 'NULL'
                rows = db.execute(f'SELECT * FROM audit WHERE id<? AND group_id IN ({marks}) ORDER BY id DESC LIMIT 200', (before, *admin['groups']))
            return [dict(r) for r in rows]

    @app.get("/api/releases")
    def releases(admin=Depends(require("releases.read"))):
        with store.connect() as db:
            return [dict(r) for r in db.execute("SELECT * FROM releases ORDER BY created DESC")]

    @app.post("/api/releases")
    async def upload_release(version: str, file: UploadFile, admin=Depends(require("releases.write"))):
        if not re.fullmatch(r"\d{1,4}\.\d{1,4}\.\d{1,4}", version):
            raise HTTPException(422, "Use a numeric version such as 1.5.1")
        identifier = str(uuid.uuid4())
        path = store.directory / "releases" / (identifier + ".exe")
        sha, size = hashlib.sha256(), 0
        try:
            with path.open("xb") as output:
                first = True
                while chunk := await file.read(1024 * 1024):
                    if first and not chunk.startswith(b"MZ"):
                        raise HTTPException(422, "Expected a Windows executable")
                    first = False
                    size += len(chunk)
                    if size > 190 * 1024 * 1024:
                        raise HTTPException(413, "Maximum release size is 190 MiB")
                    sha.update(chunk)
                    output.write(chunk)
            if not size:
                raise HTTPException(422, "Empty release")
            with store.connect() as db:
                if db.execute("SELECT 1 FROM releases WHERE version=?", (version,)).fetchone():
                    raise HTTPException(409, "Version already exists")
                db.execute("INSERT INTO releases VALUES (?,?,?,?,?,0)", (identifier, version, sha.hexdigest(), size, int(time.time())))
                store.audit(db, admin["username"], "release.upload", identifier)
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return {"id": identifier, "sha256": sha.hexdigest(), "size": size}

    @app.post("/api/releases/{identifier}/publish")
    def publish(identifier: str, admin=Depends(require("releases.write"))):
        with store.connect() as db:
            row = db.execute("SELECT * FROM releases WHERE id=?", (identifier,)).fetchone()
            if not row:
                raise HTTPException(404, "Release not found")
            current = db.execute("SELECT version FROM releases WHERE published=1").fetchone()
            if current and tuple(map(int, row["version"].split("."))) <= tuple(map(int, current[0].split("."))):
                raise HTTPException(409, "Publish a newer version; downgrades are refused")
            db.execute("UPDATE releases SET published=0")
            db.execute("UPDATE releases SET published=1 WHERE id=?", (identifier,))
            store.audit(db, admin["username"], "release.publish", identifier)
        return {"ok": True}

    @app.get("/api/agent/release")
    def agent_release(device=Depends(device_auth)):
        with store.connect() as db:
            row = db.execute("SELECT * FROM releases WHERE published=1").fetchone()
        payload = {"schema": 1, "device_id": device["id"], "release": None}
        if row:
            payload["release"] = {k: row[k] for k in ("id", "version", "sha256", "size")}
        return store.sign(payload)

    @app.get("/api/agent/releases/{identifier}")
    def download(identifier: str, device=Depends(device_auth)):
        with store.connect() as db:
            row = db.execute("SELECT * FROM releases WHERE id=? AND published=1", (identifier,)).fetchone()
        if not row:
            raise HTTPException(404, "Release not available")
        return FileResponse(store.directory / "releases" / (row["id"] + ".exe"), filename="BamdadDesk-" + row["version"] + ".exe", media_type="application/octet-stream")

    app.include_router(reporting_router(store, require, device_auth, effective_policy))
    app.include_router(administration_router(store, require, group_exists))
    app.include_router(reports_router(store, require))
    app.include_router(organization_router(store, require, device_auth, group_exists))
    app.mount("/", StaticFiles(directory=static, html=True), name="ui")
    return app
