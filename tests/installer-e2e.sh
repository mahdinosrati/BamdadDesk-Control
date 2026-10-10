#!/usr/bin/env bash
set -Eeuo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
printf '127.0.0.1 desk.bamdad.test\n' | sudo tee -a /etc/hosts >/dev/null
cat > "$RUNNER_TEMP/Caddyfile.test" <<'EOF'
{
    auto_https disable_redirects
}
https://desk.bamdad.test:18443 {
    tls internal
    reverse_proxy 127.0.0.1:18080
}
EOF
docker run -d --name existing-proxy --network host -v "$RUNNER_TEMP/Caddyfile.test:/etc/caddy/Caddyfile:ro" caddy:2.11.7-alpine
started=$(docker inspect --format '{{.State.StartedAt}}' existing-proxy)
for _attempt in {1..30}; do
    if docker cp existing-proxy:/data/caddy/pki/authorities/local/root.crt "$RUNNER_TEMP/bamdad-ci.crt" 2>/dev/null; then break; fi
    sleep 1
done
sudo install -m 0644 "$RUNNER_TEMP/bamdad-ci.crt" /usr/local/share/ca-certificates/bamdad-ci.crt
sudo update-ca-certificates
python tests/installer-e2e.py
origin=https://desk.bamdad.test:18443
if [[ ${TEST_HTTP:-0} == 1 ]]; then origin=http://127.0.0.1:18080; fi
curl -fsS "$origin/healthz"
sudo bash /opt/bamdaddesk-control/manage.sh backup /tmp/bamdad-ci-backups
sudo bash -c 'cd /tmp/bamdad-ci-backups && sha256sum --check ./*.sha256'
sudo bash -c 'tar -tzf /tmp/bamdad-ci-backups/*.tar.gz' | grep -F '.env' >/dev/null
curl -fsS --retry 5 --retry-all-errors --retry-delay 2 "$origin/healthz"
[[ "$(docker inspect --format '{{.State.StartedAt}}' existing-proxy)" == "$started" ]]
echo 'Interactive install, trusted HTTPS, backup/restart and existing-proxy coexistence passed.'
