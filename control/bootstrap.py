"""Create the first admin without placing its password on a command line."""
import argparse
import base64
import getpass
import hashlib
import os
import secrets
import uuid

from .catalog import PERMISSIONS, validate_options
from .storage import PASSWORDS, Store, canonical


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=os.environ.get("BAMDAD_DATA", "./data"))
    args = parser.parse_args()
    store = Store(args.data)
    with store.connect() as db:
        if db.execute("SELECT 1 FROM admins LIMIT 1").fetchone():
            print("Already initialized; use the panel to manage administrators.")
            return
        username = input("Administrator username: ").strip()
        password = getpass.getpass("Administrator password (12+ characters): ")
        confirmation = getpass.getpass("Repeat password: ")
        if not username or len(username) > 80 or len(password) < 12 or len(password) > 256 or password != confirmation:
            raise SystemExit("Invalid username/password or passwords do not match; nothing was changed.")
        options = {"verification-method": "use-both-passwords", "access-mode": "custom", "approve-mode": "password"}
        print("Initial organization policy (leave server fields blank to keep client defaults):")
        for key, prompt in [("custom-rendezvous-server", "ID server hostname: "),
                            ("relay-server", "Relay hostname:port: "),
                            ("key", "hbbs public key (not the panel signing key): ")]:
            value = input(prompt).strip()
            if value:
                options[key] = value
        try:
            validate_options(options)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        remote_password = getpass.getpass("Managed permanent remote password (blank = keep client preset): ")
        remote_preset = None
        if remote_password:
            if len(remote_password) > 128 or remote_password != getpass.getpass("Repeat remote password: "):
                raise SystemExit("Remote passwords do not match or exceed 128 characters; nothing was changed.")
            salt = secrets.token_hex(16)
            remote_preset = canonical({"storage": "00" + base64.b64encode(hashlib.sha256((remote_password + salt).encode()).digest()).decode(), "salt": salt})
        db.execute("INSERT INTO admins(id,username,password,permissions) VALUES (?,?,?,?)",
                   (str(uuid.uuid4()), username, PASSWORDS.hash(password), canonical(PERMISSIONS)))
        revision = store.bump(db)
        db.execute("INSERT INTO policies VALUES ('global',?,?,?)", (canonical(options), remote_preset, revision))
        store.audit(db, username, "bootstrap", "global")
    print("Administrator created. Device policy public key: " + store.public_key())


if __name__ == "__main__":
    main()
