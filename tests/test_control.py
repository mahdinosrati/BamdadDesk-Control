import base64
import hashlib
import json

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from fastapi.testclient import TestClient

from control.app import create_app
from control.catalog import PERMISSIONS
from control.storage import PASSWORDS, canonical


def test_interactive_bootstrap_creates_usable_admin_and_initial_policy(tmp_path, monkeypatch):
    from control import bootstrap

    answers = iter(["first-admin", "remote.example.com", "remote.example.com:21117", ""])
    passwords = iter(["local-test-admin-password", "local-test-admin-password", "test-remote", "test-remote"])
    monkeypatch.setattr("sys.argv", ["bootstrap", "--data", str(tmp_path)])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    monkeypatch.setattr(bootstrap.getpass, "getpass", lambda _: next(passwords))
    bootstrap.main()
    app = create_app(tmp_path, secure=False)
    with TestClient(app) as client:
        login = client.post("/api/login", json={"username": "first-admin", "password": "local-test-admin-password"})
        assert login.status_code == 200
        client.headers["x-csrf-token"] = login.json()["csrf"]
        device, _ = enroll(client)
        policy = verify(heartbeat(client, device["token"]).json(), app.state.store)
        assert policy["options"]["custom-rendezvous-server"] == "remote.example.com"
        assert policy["options"]["verification-method"] == "use-both-passwords"
        preset = policy["password"]
        expected = "00" + base64.b64encode(hashlib.sha256(("test-remote" + preset["salt"]).encode()).digest()).decode()
        assert preset["storage"] == expected


@pytest.fixture
def panel(tmp_path):
    app = create_app(tmp_path, secure=False)
    with app.state.store.connect() as db:
        db.execute("INSERT INTO admins VALUES (?,?,?,?,1)", ("owner", "owner", PASSWORDS.hash("test-only-password"), canonical(PERMISSIONS)))
    with TestClient(app) as client:
        response = client.post("/api/login", json={"username": "owner", "password": "test-only-password"})
        assert response.status_code == 200
        client.headers["x-csrf-token"] = response.json()["csrf"]
        yield client, app.state.store


def enroll(client, **kwargs):
    response = client.post("/api/enrollments", json={"label": "test", **kwargs})
    assert response.status_code == 200
    token = response.json()["token"]
    response = client.post("/api/agent/enroll", json={"token": token, "name": "Workstation", "version": "1.5.0"})
    assert response.status_code == 200
    return response.json(), token


def verify(envelope, store):
    payload = base64.b64decode(envelope["payload"])
    key = Ed25519PublicKey.from_public_bytes(base64.b64decode(store.public_key()))
    key.verify(base64.b64decode(envelope["signature"]), payload)
    return json.loads(payload)


def heartbeat(client, token, **kwargs):
    return client.post("/api/agent/heartbeat", headers={"Authorization": "Bearer " + token},
                       json={"name": "Workstation", "version": "1.5.0", **kwargs})


def test_auth_csrf_rbac_and_revocation(panel):
    client, store = panel
    assert client.post("/api/groups", json={"name": "blocked"}, headers={"x-csrf-token": "bad"}).status_code == 403
    assert client.post("/api/groups", json={"name": "blocked"}, headers={"origin": "https://evil.invalid"}).status_code == 403
    admin = client.post("/api/admins", json={"username": "viewer", "password": "viewer-test-only", "permissions": ["devices.read"]}).json()
    viewer = TestClient(client.app)
    result = viewer.post("/api/login", json={"username": "viewer", "password": "viewer-test-only"})
    viewer.headers["x-csrf-token"] = result.json()["csrf"]
    assert viewer.get("/api/devices").status_code == 200
    assert viewer.get("/api/admins").status_code == 403
    assert viewer.post("/api/enrollments", json={"label": "bad"}).status_code == 403
    assert client.put("/api/admins/" + admin["id"], json={"permissions": ["devices.read"], "active": False}).status_code == 200
    assert viewer.get("/api/devices").status_code == 401
    assert client.put("/api/admins/owner", json={"permissions": [], "active": False}).status_code == 409


def test_signed_policy_ack_password_redaction_and_single_use_token(panel):
    client, store = panel
    device, token = enroll(client)
    assert client.post("/api/agent/enroll", json={"token": token, "name": "Duplicate", "version": "1.5.0"}).status_code == 401
    policy = client.get("/api/policies/global").json()
    result = client.put("/api/policies/global", json={"options": {"enable-clipboard": "N", "verification-method": "use-both-passwords"}, "password": "remote-test-only", "expected_revision": policy["revision"]})
    assert result.status_code == 200
    revision = result.json()["revision"]
    envelope = heartbeat(client, device["token"]).json()
    payload = verify(envelope, store)
    assert payload["device_id"] == device["device_id"]
    assert payload["options"]["enable-clipboard"] == "N"
    assert payload["password"]["storage"].startswith("00")
    assert "remote-test-only" not in json.dumps(envelope)
    visible = client.get("/api/policies/global").json()
    assert visible["has_password"] is True and "password" not in visible
    assert client.get("/api/devices").json()["devices"][0]["applied"] == 0
    assert heartbeat(client, device["token"], applied=revision).status_code == 200
    assert client.get("/api/devices").json()["devices"][0]["applied"] == revision
    assert heartbeat(client, device["token"], applied=revision + 1).status_code == 422
    assert "remote-test-only" not in client.get("/api/audit").text


def test_group_and_device_overrides_and_stale_edits(panel):
    client, store = panel
    group = client.post("/api/groups", json={"name": "Finance"}).json()["id"]
    device, _ = enroll(client, group_id=group)
    for scope, options in [("global", {"enable-audio": "N", "enable-keyboard": "Y"}),
                           ("group:" + group, {"enable-keyboard": "N"}),
                           ("device:" + device["device_id"], {"enable-audio": "Y"})]:
        revision = client.get("/api/policies/" + scope).json()["revision"]
        assert client.put("/api/policies/" + scope, json={"options": options, "expected_revision": revision}).status_code == 200
    options = verify(heartbeat(client, device["token"]).json(), store)["options"]
    assert options["enable-audio"] == "Y" and options["enable-keyboard"] == "N"
    assert client.put("/api/policies/global", json={"options": {}, "expected_revision": 1}).status_code == 409
    revision = client.get("/api/policies/global").json()["revision"]
    assert client.put("/api/policies/global", json={"options": {"execute-command": "bad"}, "expected_revision": revision}).status_code == 422
    assert client.put("/api/devices/" + device["device_id"], json={"active": False}).status_code == 200
    assert heartbeat(client, device["token"]).status_code == 401


def test_release_draft_signature_checksum_publish_and_download(panel):
    client, store = panel
    device, _ = enroll(client)
    headers = {"Authorization": "Bearer " + device["token"]}
    content = b"MZ" + b"test artifact; not an executable" * 10
    release = client.post("/api/releases?version=1.5.1", files={"file": ("test.exe", content, "application/octet-stream")})
    assert release.status_code == 200
    identifier = release.json()["id"]
    assert verify(client.get("/api/agent/release", headers=headers).json(), store)["release"] is None
    assert client.get("/api/agent/releases/" + identifier, headers=headers).status_code == 404
    assert client.post("/api/releases/" + identifier + "/publish").status_code == 200
    manifest = verify(client.get("/api/agent/release", headers=headers).json(), store)["release"]
    assert manifest["sha256"] == hashlib.sha256(content).hexdigest()
    assert client.get("/api/agent/releases/" + identifier, headers=headers).content == content
    assert client.get("/api/agent/releases/" + identifier).status_code == 401
    assert client.post("/api/releases/" + identifier + "/publish").status_code == 409
    assert client.post("/api/releases?version=1.5.2", files={"file": ("bad.exe", b"not a PE")}).status_code == 422


def test_login_rate_limit_and_static_headers(panel):
    client, store = panel
    for _ in range(10):
        assert client.post("/api/login", json={"username": "no", "password": "bad"}).status_code == 401
    assert client.post("/api/login", json={"username": "owner", "password": "test-only-password"}).status_code == 429
    response = client.get("/")
    assert response.status_code == 200
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert 'lang="en"' in response.text


def test_shared_schema_and_chunked_body_limits(panel):
    from pathlib import Path
    from control.catalog import catalog
    client, store = panel
    assert json.loads((Path(__file__).parents[1] / "policy-schema.json").read_text(encoding="utf-8")) == catalog()
    response = client.post("/api/login", content=iter([b'{"username":"' + b'a' * 70000, b'","password":"bad"}']),
                           headers={"Content-Type": "application/json"})
    assert response.status_code == 413
