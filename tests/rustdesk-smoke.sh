#!/usr/bin/env bash
set -Eeuo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
export RUSTDESK_VERSION=1.1.16 RUSTDESK_HOST=127.0.0.1 RUSTDESK_ID_PORT=23116 RUSTDESK_NAT_PORT=23115 RUSTDESK_RELAY_PORT=23117
sudo install -d -m 0700 /var/lib/bamdaddesk-rustdesk/data
docker compose -f compose.rustdesk.yaml config --quiet
trap 'docker compose -f compose.rustdesk.yaml logs --tail 30; docker compose -f compose.rustdesk.yaml down' EXIT
docker compose -f compose.rustdesk.yaml up -d
for _attempt in {1..30}; do
    if sudo test -s /var/lib/bamdaddesk-rustdesk/data/id_ed25519.pub; then break; fi
    sleep 1
done
sudo test -s /var/lib/bamdaddesk-rustdesk/data/id_ed25519.pub
[[ $(docker compose -f compose.rustdesk.yaml ps --status running --services | wc -l) == 2 ]]
key=$(sudo cat /var/lib/bamdaddesk-rustdesk/data/id_ed25519.pub)
docker compose -f compose.rustdesk.yaml restart
[[ $(sudo cat /var/lib/bamdaddesk-rustdesk/data/id_ed25519.pub) == "$key" ]]
echo 'RustDesk OSS starts on selected ports and preserves its key across restart.'
