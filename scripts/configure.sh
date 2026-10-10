#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
source scripts/install-lib.sh
mode='' domain='' https_port='' proxy_port='' email='' ready='' http_port=''
data_dir=/var/lib/bamdaddesk-control
if [[ -f .env ]]; then
    data_dir=$(sed -n 's/^BAMDAD_DATA_DIR=//p' .env)
    [[ "$data_dir" =~ ^/[a-zA-Z0-9/_-]+$ && "$data_dir" != / ]] || fail 'Invalid existing data directory; preserve .env and repair it manually.'
    export BAMDAD_RECONFIGURE=1
fi
printf '\n1) Automatic HTTPS: DNS domain and public certificate\n2) Existing HTTPS reverse proxy: domain or IPv4\n3) HTTP: domain or IPv4, no DNS/certificate required for IP (unencrypted; testing only)\n'
while :; do
    ask mode 'Mode' 1
    [[ "$mode" == 1 || "$mode" == 2 || "$mode" == 3 ]] && break
done
while :; do
    if [[ "$mode" == 1 ]]; then
        ask domain 'Panel DNS hostname (no scheme, port or path)'
        valid_domain "$domain" && break
    else
        ask domain 'Panel hostname or IPv4 address (no scheme, port or path)'
        valid_host "$domain" && break
    fi
    printf 'Enter a valid hostname or, where supported, IPv4 address.\n'
done
if [[ "$mode" == 1 ]]; then
    port_available 80 || fail 'TCP 80 is occupied. Choose HTTP or your existing reverse proxy instead.'
    getent ahosts "$domain" >/dev/null || fail 'Domain does not resolve. Set DNS or choose HTTP with an IP.'
    while :; do
        ask_port https_port 'Public HTTPS port (not 80)' 443
        [[ "$https_port" != 80 ]] && break
    done
    while :; do
        ask email 'Email for TLS certificate notices'
        [[ "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]] && break
    done
    printf 'DNS A/AAAA must point here. Allow inbound TCP 80 and %s.\n' "$https_port"
    ask ready 'DNS and external firewall ready? (yes/no)' no
    [[ "$ready" == yes ]] || fail 'Prepare DNS/firewall or choose HTTP with an IP.'
    files=compose.yaml:compose.https.yaml
elif [[ "$mode" == 2 ]]; then
    while :; do
        ask https_port 'HTTPS port on your existing reverse proxy' 443
        valid_port "$https_port" && break
    done
    while :; do
        ask_port proxy_port 'Local backend port for your reverse proxy' 18080
        [[ "$proxy_port" != "$https_port" ]] && break
        printf 'Backend and HTTPS ports must differ.\n'
    done
    files=compose.yaml:compose.proxy.yaml
else
    printf 'HTTP sends login and management data without encryption. Managed Windows clients require HTTPS.\n'
    ask_port http_port 'Public HTTP port' 8080
    files=compose.yaml:compose.http.yaml
fi
if [[ "$mode" == 3 ]]; then
    origin="http://$domain"
    [[ "$http_port" == 80 ]] || origin+=":$http_port"
else
    origin="https://$domain"
    [[ "$https_port" == 443 ]] || origin+=":$https_port"
fi
[[ ! -f .env ]] || cp -p .env ".env.backup.$(date -u +%Y%m%dT%H%M%S%N)"
cat > .env <<EOF
COMPOSE_FILE=$files
BAMDAD_ORIGIN=$origin
BAMDAD_DOMAIN=$domain
BAMDAD_DATA_DIR=$data_dir
BAMDAD_HTTPS_PORT=${https_port:-443}
BAMDAD_PROXY_PORT=${proxy_port:-18080}
BAMDAD_HTTP_PORT=${http_port:-8080}
BAMDAD_TLS_EMAIL=$email
EOF
chmod 0600 .env
printf '\nConfigured panel URL: %s\n' "$origin"
if [[ "$mode" == 2 ]]; then
    printf 'Route your HTTPS proxy to http://127.0.0.1:%s\n' "$proxy_port"
fi
