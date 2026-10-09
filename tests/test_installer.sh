#!/usr/bin/env bash
set -Eeuo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
source scripts/install-lib.sh
for port in 1 443 8443 65535; do valid_port "$port"; done
for port in 0 65536 080 abc '443;id' -1; do
    if valid_port "$port"; then echo "Invalid port accepted: $port"; exit 1; fi
done
for domain in desk.example.com remote-1.example.org; do valid_domain "$domain"; done
for domain in localhost '-bad.example.com' 'https://desk.example.com' 'a..com' 'a.com.' 'a.com:443' '127.0.0.1' 'a.com${X}'; do
    if valid_domain "$domain"; then echo "Invalid domain accepted: $domain"; exit 1; fi
done
ss() { printf '%s' "${MOCK_LISTENERS:-}"; }
docker() { printf '%s' "${MOCK_PUBLISHED:-}"; }
port_available 8443
MOCK_LISTENERS='LISTEN 0 128 0.0.0.0:8443'
if port_available 8443; then echo 'Listening socket missed'; exit 1; fi
MOCK_LISTENERS=''
MOCK_PUBLISHED='0.0.0.0:8443->443/tcp, [::]:8443->443/tcp'
if port_available 8443; then echo 'Docker NAT publication missed'; exit 1; fi
port_available 443
echo 'Installer input and occupied-port checks passed.'
