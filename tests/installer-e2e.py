"""Exercise the interactive wizard on a disposable GitHub Linux runner."""
import os
from pathlib import Path
import subprocess

import pexpect


root = Path(__file__).resolve().parents[1]
subprocess.run(["git", "tag", "installer-test"], check=True)
script = (root / "install.sh").read_text()
script = script.replace("https://github.com/mahdinosrati/BamdadDesk-Control.git", str(root))
script = script.replace("readonly RELEASE=v1.0.0-pilot.1", "readonly RELEASE=installer-test")
test_script = Path(os.environ["RUNNER_TEMP"]) / "install-test.sh"
test_script.write_text(script)
child = pexpect.spawn("sudo", ["bash", str(test_script)], timeout=600, encoding="utf-8")
answers = [
    ("Mode", "2"),
    ("Panel DNS hostname", "desk.bamdad.test"),
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
try:
    for prompt, answer in answers:
        child.expect_exact(prompt)
        child.sendline(answer)
    child.expect_exact("Panel is reachable: https://desk.bamdad.test:18443")
    child.expect(pexpect.EOF)
    child.close()
    assert child.exitstatus == 0, child.exitstatus
except Exception:
    print(child.before)
    child.close(force=True)
    raise

print("Interactive installation completed through verified HTTPS.")
