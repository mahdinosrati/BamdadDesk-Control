"""Exercise the interactive wizard on a disposable GitHub Linux runner."""
import os
from pathlib import Path
import subprocess

import pexpect


root = Path(__file__).resolve().parents[1]
subprocess.run(["git", "tag", "installer-test"], check=True)
script = (root / "install.sh").read_text()
script = script.replace("https://github.com/mahdinosrati/BamdadDesk-Control.git", str(root))
script = script.replace("readonly RELEASE=v1.1.0-pilot.1", "readonly RELEASE=installer-test")
test_script = Path(os.environ["RUNNER_TEMP"]) / "install-test.sh"
test_script.write_text(script)
child = pexpect.spawn("sudo", ["bash", str(test_script)], timeout=600, encoding="utf-8")
http_mode = os.environ.get("TEST_HTTP") == "1"
answers = [
    ("Mode", "2"),
    ("Panel hostname or IPv4 address", "desk.bamdad.test"),
    ("HTTPS port on your existing reverse proxy", "18443"),
    ("Local backend port", "18080"),
    ("Administrator username:", "ci-admin"),
    ("Administrator password", "ci-disposable-admin-password"),
    ("Repeat password:", "ci-disposable-admin-password"),
    ("ID server hostname:", ""),
    ("Relay hostname:port:", ""),
    ("hbbs public key", ""),
    ("Managed permanent remote password", ""),
]
if http_mode:
    answers[:4] = [("Mode", "3"), ("Panel hostname or IPv4 address", "127.0.0.1"), ("Public HTTP port", "18080")]
origin = "http://127.0.0.1:18080" if http_mode else "https://desk.bamdad.test:18443"
try:
    for prompt, answer in answers:
        child.expect_exact(prompt)
        child.sendline(answer)
    child.expect_exact("Panel is reachable: " + origin)
    child.expect(pexpect.EOF)
    child.close()
    assert child.exitstatus == 0, child.exitstatus
except Exception:
    print(child.before)
    child.close(force=True)
    raise

print("Interactive installation completed through " + origin)
