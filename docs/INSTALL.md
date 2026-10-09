# Installation

## Scope and prerequisites

The interactive installer supports Ubuntu 22.04/24.04 and Debian 12/13 with systemd. Docker must support Linux containers. Automatic Compose binary installation supports x86_64/aarch64. CI exercises Linux x86_64 containers; arm64 and full fresh-host apt installation are not yet validated.

Use the one-command installer in [README](../README.md). It fetches the tagged pilot release over HTTPS. It installs OS dependencies, uses Docker's official apt repository when no engine is present, and installs a checksum-verified Compose v5.6.0 plugin when needed. It does not remove conflicting packages, replace a running engine, restart existing Docker or configure a provider firewall.

Existing Compose must support `up --wait` (2.20+). Unsupported or broken installations stop with an explanation. Outbound access to GitHub, Docker repositories, Docker Hub, PyPI and certificate authorities is required. Restrictive networks need their own approved mirrors.

## Automatic HTTPS

Create DNS A/AAAA records for `desk.example.com`. Remove stale AAAA records if IPv6 cannot reach the server. Inbound TCP 80 and the chosen HTTPS port must reach the host. Choose mode 1 and enter hostname, HTTPS port (443 by default), email and administrator credentials.

Caddy listens on container port 443; Docker maps the chosen public port to it. Certificate issuance uses HTTP-01 on public port 80, including when HTTPS uses 8443. The normal HTTP-to-HTTPS redirect is disabled so it cannot redirect to the wrong port. Always open the printed **HTTPS URL**, including its port. Port 80 remains necessary for certificate renewal.

No API port is published in this mode. A port check catches listening sockets and Docker published ports before starting. Ports can still be claimed by another process between checking and startup; Compose will fail rather than stop that process.

## Existing reverse proxy

Choose mode 2 if Nginx, Caddy or another proxy already occupies ports 80/443. Enter the public hostname/HTTPS port and a free loopback backend port, such as 18080.

For **Caddy running on the host**, add:

```caddyfile
desk.example.com {
    request_body {
        max_size 200MB
    }
    reverse_proxy 127.0.0.1:18080
}
```

For **Nginx running on the host**, add these locations to an existing HTTPS server block with a valid certificate for the panel hostname:

```nginx
client_max_body_size 200m;
location / {
    proxy_pass http://127.0.0.1:18080;
    proxy_set_header Host $http_host;
    proxy_set_header X-Forwarded-Proto https;
    proxy_read_timeout 120s;
}
```

Validate your proxy configuration before reloading it. Do not use an HTTP public origin, disable Secure cookies or set `BAMDAD_DEV_HTTP=1` in production. The exact browser origin must match `BAMDAD_ORIGIN` in `.env`, including a nonstandard port. A proxy inside another container cannot use the host's 127.0.0.1; configure an explicitly shared Docker network manually instead. The wizard supports a **host** proxy, not automatic changes to arbitrary container proxy stacks.

The installer reports HTTPS failure until the route and certificate are ready, even if the API container is healthy. After configuring the route, verify `curl -fsS https://desk.example.com/healthz` without `-k`.

## Manual Docker deployment

On another Docker-compatible distribution, install Docker/Compose using its official instructions, clone this repository at a release tag, and create a root-owned deployment directory. Copy these values into `.env` (adjust the hostname):

```dotenv
COMPOSE_FILE=compose.yaml:compose.proxy.yaml
BAMDAD_ORIGIN=https://desk.example.com
BAMDAD_DOMAIN=desk.example.com
BAMDAD_DATA_DIR=/var/lib/bamdaddesk-control
BAMDAD_PROXY_PORT=18080
```

Then run from the repository root:

```bash
sudo install -d -m 0700 -o 10001 -g 10001 /var/lib/bamdaddesk-control
sudo chmod 0600 .env
sudo bash manage.sh resume
```

For automatic HTTPS, use `COMPOSE_FILE=compose.yaml:compose.https.yaml` and add `BAMDAD_TLS_EMAIL` and `BAMDAD_HTTPS_PORT=443`. `manage.sh backup` assumes the documented fixed data path; custom paths require an adapted backup command.

## References

- [Docker on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
- [Docker on Debian](https://docs.docker.com/engine/install/debian/)
- [Compose plugin installation](https://docs.docker.com/compose/install/linux/)
- [Caddy automatic HTTPS](https://caddyserver.com/docs/automatic-https)

Docker-published ports may bypass host UFW rules. Use appropriate provider firewall or Docker firewall controls; see the Docker installation documentation. The installer does not make firewall changes.
