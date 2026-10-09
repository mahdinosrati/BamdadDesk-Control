#!/usr/bin/env bash
set -Eeuo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
export BAMDAD_ORIGIN=https://desk.example.com
export BAMDAD_DOMAIN=desk.example.com
export BAMDAD_TLS_EMAIL=admin@example.com
export BAMDAD_DATA_DIR="$RUNNER_TEMP/bamdad-data"
export BAMDAD_PROXY_PORT=18080
export COMPOSE_FILE=compose.yaml:compose.proxy.yaml
sudo install -d -m 0700 -o 10001 -g 10001 "$BAMDAD_DATA_DIR"
docker run -d --name unrelated-service -p 127.0.0.1:21114:80 nginx:alpine
sentinel=$(docker inspect --format '{{.State.StartedAt}}' unrelated-service)
trap 'docker compose logs --tail 50; docker compose down; docker rm -f unrelated-service' EXIT
docker build -t bamdaddesk-control:local .
docker compose up -d --no-build --wait --wait-timeout 90
curl --fail --retry 3 http://127.0.0.1:18080/healthz
curl --fail http://127.0.0.1:18080/ | grep -q 'BamdadDesk'
[[ "$(docker compose port api 8000)" == 127.0.0.1:18080 ]]
[[ "$(docker inspect --format '{{.State.StartedAt}}' unrelated-service)" == "$sentinel" ]]
curl --fail http://127.0.0.1:21114/ >/dev/null
COMPOSE_FILE=compose.yaml:compose.https.yaml docker compose config --quiet
docker run --rm -e BAMDAD_DOMAIN -e BAMDAD_TLS_EMAIL -v "$PWD/Caddyfile:/etc/caddy/Caddyfile:ro" caddy:2.11.7-alpine caddy validate --config /etc/caddy/Caddyfile
echo 'Docker health, loopback exposure, coexistence and Caddy configuration passed.'
