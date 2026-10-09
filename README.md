# BamdadDesk Control

[![CI](https://github.com/mahdinosrati/BamdadDesk-Control/actions/workflows/ci.yml/badge.svg)](https://github.com/mahdinosrati/BamdadDesk-Control/actions/workflows/ci.yml)

Self-hosted management for **compatible BamdadDesk Windows clients**, with an English/Persian web panel, RTL layout and locally bundled Vazirmatn fonts.

**Pilot release.** This public repository contains the complete panel source and Docker installer. No GitHub account or private repository token is required to install it. It does not include an organization-specific Windows executable or a RustDesk Pro implementation. Unmodified RustDesk clients cannot enroll in this panel.

[فارسی](README.fa.md) · [Installation](docs/INSTALL.md) · [Operations and recovery](docs/OPERATIONS.md) · [Architecture](docs/ARCHITECTURE.md) · [Security](SECURITY.md) · [Changelog](CHANGELOG.md)

## One-command installation

Run on **Ubuntu 22.04/24.04 or Debian 12/13**, with systemd, root/sudo, internet access, a DNS hostname and a compatible Docker host (amd64/arm64). Start with 2 CPU cores, 2 GB RAM and enough disk for uploaded client releases; this is a starting configuration, not a measured capacity guarantee.

```bash
sudo bash -c 'set -e; if ! command -v curl >/dev/null; then apt-get update; apt-get install -y curl ca-certificates; fi; installer=$(mktemp); trap '\''rm -f "$installer"'\'' EXIT; curl --proto "=https" --tlsv1.2 -fsSL https://raw.githubusercontent.com/mahdinosrati/BamdadDesk-Control/v1.0.0-pilot.1/install.sh -o "$installer"; bash "$installer"'
```

In a root shell, omit `sudo`. The command installs the download prerequisite too, uses a unique temporary file, and stops if downloading fails. To inspect code before executing it, download [install.sh](https://github.com/mahdinosrati/BamdadDesk-Control/blob/v1.0.0-pilot.1/install.sh) and run `sudo bash install.sh`.

The wizard asks for:

1. Automatic HTTPS or an existing host reverse proxy.
2. Panel hostname, HTTPS port, and certificate email (automatic mode).
3. A free local backend port (existing-proxy mode).
4. Initial administrator username and password, entered privately.
5. Optional RustDesk ID server, relay, hbbs public key and managed remote password.

It installs prerequisites and Docker if absent, adds Compose if missing, builds the panel and initializes persistent storage. Existing Docker engines are reused. Conflicting Docker packages or broken installations cause an explicit error rather than package removal. No existing RustDesk container, service or firewall rule is changed.

Automatic HTTPS requires public DNS pointing to the server, free/reachable TCP **80** for certificate validation and the selected HTTPS port (default **443**). If 80 is occupied, choose existing reverse proxy mode: it publishes the backend on **127.0.0.1** only. You must add a route to your existing proxy; the installer cannot safely guess or modify its configuration. See [examples](docs/INSTALL.md#existing-reverse-proxy).

## What it does

- Device inventory, groups, aliases, notes, online status and policy application status.
- Administrator permissions and group scopes enforced by the API.
- Global, group and device policies for supported server settings, access permissions and remote password methods.
- Limited-use, expiring enrollment tokens and separate credentials per device.
- Ed25519-signed policies and signed update manifests; client release upload and SHA256 verification.
- Dashboard charts, client-reported connection events and administrator audit history.
- English by default, Persian/RTL with Vazirmatn; no external font CDN.

Remote desktop traffic still uses your existing **hbbs/hbbr** server. Browser remote desktop, SSO/MFA and automatic integration with stock RustDesk are not implemented. Remote permissions are limited to the published [policy catalog](policy-schema.json), not every future RustDesk option.

## Connect a client

Use a managed BamdadDesk client implementing the [protocol](docs/ARCHITECTURE.md). Install its Windows service, create an enrollment token in the panel, then run [client/Register-Client.ps1](client/Register-Client.ps1) as a Windows administrator. Enter the panel HTTPS origin, signing public key and enrollment token. Verify both heartbeat and **applied policy revision** in the panel. Installing this panel alone does not add management support to an existing RustDesk executable.

## Operations

```bash
sudo bash /opt/bamdaddesk-control/manage.sh status
sudo bash /opt/bamdaddesk-control/manage.sh logs
sudo bash /opt/bamdaddesk-control/manage.sh backup /srv/bamdad-backups
```

Source/configuration: `/opt/bamdaddesk-control`. Database, signing key and uploaded releases: `/var/lib/bamdaddesk-control`. See [backup, restore, upgrade and failure recovery](docs/OPERATIONS.md) before production use.

## Development

Python 3.12:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.lock
python -m pytest -q
python -m control.bootstrap
BAMDAD_DEV_HTTP=1 uvicorn control.app:create_app --factory --host 127.0.0.1 --port 8791
```

HTTP development mode is loopback-only and cannot be used by managed clients. Regenerate `policy-schema.json` with `python export_schema.py` after catalog changes and coordinate compatible client changes. See [contributing](CONTRIBUTING.md).

## License and attribution

AGPL-3.0: [LICENSE](LICENSE). Font licensing and upstream attribution: [NOTICE](NOTICE). This is an independent project, not an official RustDesk product. There is no RustDesk Pro license requirement for this panel; it also does not supply Pro features or Pro protocol compatibility.
