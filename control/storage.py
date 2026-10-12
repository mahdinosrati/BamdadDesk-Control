import base64
import hashlib
import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from argon2 import PasswordHasher
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat, NoEncryption

PASSWORDS = PasswordHasher()


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


class Store:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.database = self.directory / "control.sqlite3"
        (self.directory / "releases").mkdir(exist_ok=True)
        self.keyfile = self.directory / "signing.key"
        if not self.keyfile.exists():
            key = Ed25519PrivateKey.generate().private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
            fd = os.open(self.keyfile, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as file:
                file.write(key)
        self.key = Ed25519PrivateKey.from_private_bytes(self.keyfile.read_bytes())
        with self.connect() as db:
            db.executescript('''
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS admins (
                    id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
                    permissions TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1);
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY, admin TEXT NOT NULL, csrf TEXT NOT NULL, expires INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS login_attempts (
                    address TEXT PRIMARY KEY, count INTEGER NOT NULL, started INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS groups (
                    id TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL);
                CREATE TABLE IF NOT EXISTS devices (
                    id TEXT PRIMARY KEY, token TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
                    group_id TEXT NOT NULL DEFAULT '', rustdesk_id TEXT NOT NULL DEFAULT '',
                    version TEXT NOT NULL DEFAULT '', last_seen INTEGER NOT NULL DEFAULT 0,
                    applied INTEGER NOT NULL DEFAULT 0, error TEXT NOT NULL DEFAULT '',
                    active INTEGER NOT NULL DEFAULT 1);
                CREATE TABLE IF NOT EXISTS enrollments (
                    token TEXT PRIMARY KEY, label TEXT NOT NULL, group_id TEXT NOT NULL,
                    expires INTEGER NOT NULL, remaining INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS policies (
                    scope TEXT PRIMARY KEY, options TEXT NOT NULL, password TEXT,
                    revision INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value INTEGER NOT NULL);
                INSERT OR IGNORE INTO meta VALUES ('revision', 1);
                CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY, created INTEGER NOT NULL,
                    actor TEXT NOT NULL, action TEXT NOT NULL, target TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS releases (
                    id TEXT PRIMARY KEY, version TEXT UNIQUE NOT NULL, sha256 TEXT NOT NULL,
                    size INTEGER NOT NULL, created INTEGER NOT NULL, published INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS admin_scopes (admin TEXT PRIMARY KEY, groups_json TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS device_details (
                    device TEXT PRIMARY KEY, alias TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '',
                    platform TEXT NOT NULL DEFAULT '', username TEXT NOT NULL DEFAULT '');
                CREATE TABLE IF NOT EXISTS connection_events (
                    id INTEGER PRIMARY KEY, event_id TEXT UNIQUE NOT NULL, device TEXT NOT NULL,
                    group_id TEXT NOT NULL, session_id TEXT NOT NULL, kind TEXT NOT NULL,
                    occurred INTEGER NOT NULL, received INTEGER NOT NULL, peer_id TEXT NOT NULL,
                    peer_name TEXT NOT NULL, peer_ip TEXT NOT NULL, connection_type INTEGER NOT NULL);
                CREATE INDEX IF NOT EXISTS connection_device_time ON connection_events(device,occurred);
                CREATE INDEX IF NOT EXISTS connection_group_time ON connection_events(group_id,occurred);
                CREATE INDEX IF NOT EXISTS connection_session ON connection_events(device,session_id,group_id,kind,occurred);
            ''')
            if 'group_id' not in {r[1] for r in db.execute('PRAGMA table_info(audit)')}:
                db.execute("ALTER TABLE audit ADD COLUMN group_id TEXT NOT NULL DEFAULT ''")
            db.executescript('''
                CREATE TABLE IF NOT EXISTS enrollment_details (
                    token TEXT PRIMARY KEY, id TEXT UNIQUE NOT NULL,
                    created INTEGER NOT NULL DEFAULT 0, used INTEGER,
                    revoked INTEGER NOT NULL DEFAULT 0);
                INSERT OR IGNORE INTO enrollment_details(token,id)
                    SELECT token,lower(hex(randomblob(16))) FROM enrollments;
                CREATE TABLE IF NOT EXISTS organization_settings (key TEXT PRIMARY KEY,value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS automatic_enrollments (token TEXT PRIMARY KEY);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.database, timeout=20)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def public_key(self):
        return base64.b64encode(self.key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)).decode()

    def sign(self, payload):
        raw = canonical(payload).encode()
        return {"payload": base64.b64encode(raw).decode(),
                "signature": base64.b64encode(self.key.sign(raw)).decode()}

    @staticmethod
    def audit(db, actor, action, target, group_id=''):
        db.execute("INSERT INTO audit(created,actor,action,target,group_id) VALUES (?,?,?,?,?)",
                   (int(time.time()), actor, action, target, group_id))

    @staticmethod
    def bump(db):
        db.execute("UPDATE meta SET value=value+1 WHERE key='revision'")
        return db.execute("SELECT value FROM meta WHERE key='revision'").fetchone()[0]
