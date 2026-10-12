import json
import os
import secrets
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.background import BackgroundTask

from .scopes import require_global, require_group
from .storage import digest


class Settings(BaseModel):
    model_config = ConfigDict(extra='forbid')
    api_url: str = Field(max_length=300)
    automatic_enrollment: bool = False


class Package(BaseModel):
    model_config = ConfigDict(extra='forbid')
    label: str = Field(min_length=1, max_length=100)
    group_id: str = Field(default='', max_length=40)
    hours: int = Field(default=168, ge=1, le=8760)
    uses: int = Field(default=100, ge=1, le=10000)
    release_id: str = Field(max_length=40)


def https_origin(value):
    try:
        url = urlsplit(value)
        port = url.port
    except ValueError as exc:
        raise HTTPException(422, 'Invalid API origin') from exc
    if url.scheme != 'https' or not url.hostname or url.username or url.password or url.path not in ('', '/') or url.query or url.fragment or any(c.isspace() for c in value):
        raise HTTPException(422, 'API must be an HTTPS origin without credentials, path or query')
    return value.rstrip('/')


def settings(db):
    row = db.execute("SELECT value FROM organization_settings WHERE key='management'").fetchone()
    return json.loads(row['value']) if row else {'api_url': os.environ.get('BAMDAD_ORIGIN', ''), 'automatic_enrollment': False}


def router(store, require, device_auth, group_exists):
    routes = APIRouter()

    @routes.get('/api/organization')
    def get_settings(admin=Depends(require('enrollment.write'))):
        require_global(admin)
        with store.connect() as db:
            return {**settings(db), 'public_key': store.public_key()}

    @routes.put('/api/organization')
    def save_settings(body: Settings, admin=Depends(require('enrollment.write'))):
        require_global(admin)
        value = {'api_url': https_origin(body.api_url), 'automatic_enrollment': body.automatic_enrollment}
        with store.connect() as db:
            db.execute("INSERT INTO organization_settings VALUES ('management',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (json.dumps(value),))
            store.audit(db, admin['username'], 'organization.update', 'management')
        return {'ok': True}

    @routes.get('/api/agent/management')
    def management(device=Depends(device_auth)):
        with store.connect() as db:
            value = settings(db)
        return store.sign({'schema': 1, 'device_id': device['id'], 'api_url': value['api_url']})

    @routes.post('/api/organization/installer')
    def installer(body: Package, admin=Depends(require('enrollment.write'))):
        require_global(admin)
        if not shutil.which('makensis'):
            raise HTTPException(503, 'NSIS compiler unavailable. Use the documented panel Docker image.')
        with store.connect() as db:
            configuration = settings(db)
            origin = https_origin(configuration['api_url'])
            if not configuration['automatic_enrollment']:
                raise HTTPException(409, 'Enable automatic enrollment before creating an installer')
            require_group(admin, body.group_id)
            group_exists(db, body.group_id)
            release = db.execute('SELECT * FROM releases WHERE id=?', (body.release_id,)).fetchone()
            if not release:
                raise HTTPException(404, 'Upload a compatible managed Windows client first')
        token = secrets.token_urlsafe(32)
        folder_root = store.directory / 'packages'
        folder_root.mkdir(exist_ok=True, mode=0o700)
        folder = Path(tempfile.mkdtemp(dir=folder_root))
        try:
            templates = Path(__file__).parent / 'installer'
            for name in ('Setup.ps1', 'Setup.nsi'):
                shutil.copyfile(templates / name, folder / name)
            shutil.copyfile(store.directory / 'releases' / (release['id'] + '.exe'), folder / 'BamdadDesk.exe')
            (folder / 'profile.json').write_text(json.dumps({'url': origin, 'public_key': store.public_key(), 'token': token, 'sha256': release['sha256']}), encoding='utf-8')
            result = subprocess.run(['makensis', '-V2', 'Setup.nsi'], cwd=folder, capture_output=True, timeout=240, check=False)
            if result.returncode != 0:
                raise HTTPException(500, 'Installer compilation failed; check compiler availability and free disk space')
            with store.connect() as db:
                # Recheck the switch after compilation, before issuing the registration grant.
                if not settings(db)['automatic_enrollment']:
                    raise HTTPException(409, 'Automatic enrollment was disabled during compilation')
                group_exists(db, body.group_id)
                db.execute('INSERT INTO enrollments VALUES (?,?,?,?,?)', (digest(token), body.label, body.group_id, int(time.time()) + body.hours * 3600, body.uses))
                db.execute('INSERT INTO enrollment_details(token,id,created,used) VALUES (?,?,?,0)', (digest(token), str(uuid.uuid4()), int(time.time())))
                db.execute('INSERT INTO automatic_enrollments VALUES (?)', (digest(token),))
                store.audit(db, admin['username'], 'installer.create', body.label, body.group_id)
            return FileResponse(folder / 'BamdadDesk-Setup.exe', filename='BamdadDesk-Setup.exe', media_type='application/octet-stream', headers={'Cache-Control': 'no-store'}, background=BackgroundTask(shutil.rmtree, folder))
        except Exception:
            shutil.rmtree(folder)
            raise

    return routes
