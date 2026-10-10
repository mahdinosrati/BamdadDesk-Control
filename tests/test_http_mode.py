import pytest
from fastapi.testclient import TestClient

from control.app import create_app
from control.catalog import PERMISSIONS
from control.storage import PASSWORDS, canonical


@pytest.mark.parametrize("allow_http", [False, True])
def test_explicit_http_mode_login_and_csrf(tmp_path, monkeypatch, allow_http):
    monkeypatch.delenv("BAMDAD_DEV_HTTP", raising=False)
    monkeypatch.setenv("BAMDAD_ALLOW_HTTP", "1" if allow_http else "0")
    origin = "http://192.0.2.10:8080" if allow_http else "https://desk.example.com"
    monkeypatch.setenv("BAMDAD_ORIGIN", origin)
    app = create_app(tmp_path)
    with app.state.store.connect() as db:
        db.execute("INSERT INTO admins VALUES (?,?,?,?,1)", ("owner", "owner", PASSWORDS.hash("test-only-password"), canonical(PERMISSIONS)))
    with TestClient(app, base_url=origin) as client:
        login = client.post("/api/login", json={"username": "owner", "password": "test-only-password"})
        assert login.status_code == 200
        assert ("; secure" in login.headers["set-cookie"].lower()) is not allow_http
        assert "httponly" in login.headers["set-cookie"].lower()
        assert client.post("/api/groups", json={"name": "test"}).status_code == 403
        client.headers["x-csrf-token"] = login.json()["csrf"]
        assert client.post("/api/groups", json={"name": "test"}).status_code == 200
        assert client.post("/api/groups", json={"name": "bad"}, headers={"origin": "http://evil.invalid"}).status_code == 403
