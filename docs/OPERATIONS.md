# Operations and recovery

Run commands from `/opt/bamdaddesk-control` as root, or use `sudo bash /opt/bamdaddesk-control/manage.sh ...`.

## Inspect and recover

- `manage.sh status`: container status and API health.
- `manage.sh logs`: recent API logs; `manage.sh logs caddy`: certificate/proxy errors in automatic mode.
- `manage.sh resume`: rebuild, create the first administrator only if absent, then start this stack. It never resets an existing administrator password.
- `curl -fsS https://YOUR-HOST/healthz`: verify public HTTPS, using the configured port. Do not bypass certificate validation.

Before `.env` is created, a failed installation normally removes its temporary source checkout; rerun the installer. Once `/opt/bamdaddesk-control/.env` exists, use `resume`. If the process was killed between moving source and writing `.env`, preserve the directory and any existing data, then complete `.env` using INSTALL.md. Never delete a populated data directory merely to rerun installation.

If port 80 is occupied, choose reverse proxy mode. If another container already uses the requested HTTPS/backend port, choose another. DNS errors require fixing A/AAAA records. A healthy API with failed public HTTPS usually indicates DNS, certificate issuance, external firewall or proxy routing problems. The first administrator requires a password of at least 12 characters.

## Backup

```bash
sudo bash /opt/bamdaddesk-control/manage.sh backup /srv/bamdad-backups
```

The API is stopped briefly to obtain a consistent database/files snapshot and restarted by an exit trap. The tar archive includes `/var/lib/bamdaddesk-control`, `.env` and `Caddyfile`. A SHA256 file and source commit file accompany it. Keep copies off the server with restricted access: the archive contains the policy signing private key, database and uploaded releases. Automatic Caddy TLS volumes are not included; on recovery Caddy obtains new certificates, so DNS/port 80 must work. The policy signing key **is** included and must be preserved.

## Restore to a replacement host

1. Install Docker/Compose, obtain the exact recorded source commit in `/opt/bamdaddesk-control`, and preserve the original backup.
2. Verify `sha256sum --check ARCHIVE.tar.gz.sha256` from the archive directory. List archive paths with `tar -tzf ARCHIVE.tar.gz`. Only restore trusted backups produced by this tool.
3. With the panel stopped, extract to a new root-only staging directory. The archive contains `bamdaddesk-control/`, `.env` and `Caddyfile`.
4. Move the restored data folder to `/var/lib/bamdaddesk-control`. If that path already exists, keep a separate recovery copy first; do not merge databases. Restore `.env` and `Caddyfile` to the source directory. Set data ownership to UID/GID 10001, directory mode 0700 and `.env` mode 0600.
5. Check hostname, DNS, `.env` and proxy routing for the new server. Run `sudo bash manage.sh resume`. Bootstrap should say it is already initialized.
6. Verify HTTPS, administrator login, signing public key and a test client's heartbeat/applied revision before reconnecting the organization.

## Upgrade

Back up first. Read the target release notes and keep the recorded source commit. From the source directory:

```bash
sudo git fetch --tags origin
sudo git checkout --detach NEW_RELEASE_TAG
sudo bash manage.sh resume
```

Do not paste `NEW_RELEASE_TAG` unchanged. Use a real reviewed release tag. This rebuilds the panel image and can briefly interrupt management access. Existing remote desktop sessions use hbbs/hbbr independently. After a database migration, reverting source alone may not roll back data; restore the matching backup if necessary. Do not reuse an old database while discarding its signing key.

Client updates are separate: upload an authorized compatible Windows executable in the panel and publish it. Clients verify signed manifests and hashes; installation requires user action. This repository does not distribute your organization's client executable.

## Removal

`sudo docker compose down` from the deployment directory stops only this project's containers and retains data/volumes. There is intentionally no automatic data-erasing uninstall command. Archive backups and decide separately whether to remove source, data and Caddy volumes. Do not remove Docker or modify hbbs/hbbr to uninstall the panel.

## Known limits

This is a pilot. Full fresh-host installation across all listed distributions, arm64, real public ACME issuance, a live managed Windows service and organization-scale load require deployment acceptance testing. CI checks API behavior, shell logic and Linux Docker health/coexistence; its results are visible in GitHub Actions. Behind the proxy, Uvicorn intentionally does not trust forwarded client IP headers: login rate limits can be shared across users. There is no MFA/SSO, browser remote desktop, automatic backup scheduling or immutable external audit store. Configure organizational access and backup policies accordingly.
