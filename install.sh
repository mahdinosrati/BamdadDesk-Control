#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

readonly REPOSITORY=https://github.com/mahdinosrati/BamdadDesk-Control.git
readonly RELEASE=v1.0.0-pilot.1
readonly DEPLOY=/opt/bamdaddesk-control
readonly DATA=/var/lib/bamdaddesk-control

die() { printf 'Error: %s\n' "$*" >&2; exit 1; }
[[ $EUID -eq 0 ]] || die 'Run this installer with sudo or from a root shell.'
[[ -r /dev/tty ]] || die 'An interactive terminal is required.'
[[ -f /etc/os-release ]] || die 'This installer supports Ubuntu and Debian.'
source /etc/os-release
case "$ID:$VERSION_ID" in
    ubuntu:22.04|ubuntu:24.04|debian:12|debian:13) ;;
    *) die 'Supported systems: Ubuntu 22.04/24.04 and Debian 12/13 (systemd). Use the manual Docker guide elsewhere.' ;;
esac
command -v systemctl >/dev/null || die 'systemd is required by the installer.'
case "$(dpkg --print-architecture)" in
    amd64|arm64) ;;
    *) die 'This installer supports amd64 and arm64.' ;;
esac
command -v flock >/dev/null || die 'Install util-linux (flock) first.'
exec 9>/run/lock/bamdaddesk-control-install.lock
flock -n 9 || die 'Another BamdadDesk installer is running.'
if [[ -e "$DEPLOY" ]]; then
    die "Deployment already exists. For a configured deployment run: sudo bash $DEPLOY/manage.sh resume. See docs/OPERATIONS.md for incomplete setup recovery."
fi
[[ ! -e "$DATA" ]] || die "$DATA already exists; refusing to overwrite existing data."

printf 'Installing BamdadDesk Control %s. Existing RustDesk services will remain running.\n' "$RELEASE"
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates curl git iproute2 dnsutils
if ! command -v docker >/dev/null; then
    for package in docker.io docker-compose docker-compose-v2 podman-docker containerd runc; do
        if dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q 'install ok installed'; then
            die "Conflicting package $package is installed. Configure Docker and Compose manually; the installer will not remove it."
        fi
    done
    install -m 0755 -d /etc/apt/keyrings
    [[ ! -e /etc/apt/sources.list.d/docker.sources && ! -e /etc/apt/sources.list.d/docker.list ]] || die 'Existing Docker apt configuration detected; install Docker from it manually.'
    curl --proto '=https' --tlsv1.2 -fsSL "https://download.docker.com/linux/$ID/gpg" -o /etc/apt/keyrings/bamdad-docker.asc
    chmod 0644 /etc/apt/keyrings/bamdad-docker.asc
    cat > /etc/apt/sources.list.d/bamdad-docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/$ID
Suites: $VERSION_CODENAME
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/bamdad-docker.asc
EOF
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable --now docker
fi
docker info >/dev/null 2>&1 || die 'Existing Docker is not reachable. Start it manually; this installer does not restart existing daemons.'
if ! docker compose version >/dev/null 2>&1; then
    case "$(uname -m)" in
        x86_64) compose_arch=x86_64 ;;
        aarch64) compose_arch=aarch64 ;;
        *) die 'Automatic Compose installation supports x86_64 and aarch64 only.' ;;
    esac
    compose_version=v5.6.0
    plugin_dir=/usr/local/lib/docker/cli-plugins
    install -d -m 0755 "$plugin_dir"
    [[ ! -e "$plugin_dir/docker-compose" ]] || die 'An existing Compose plugin is broken; repair it before retrying.'
    download=$(mktemp -d)
    trap 'rm -rf -- "$download"' EXIT
    asset="docker-compose-linux-$compose_arch"
    curl --proto '=https' --tlsv1.2 -fsSL "https://github.com/docker/compose/releases/download/$compose_version/$asset" -o "$download/$asset"
    curl --proto '=https' --tlsv1.2 -fsSL "https://github.com/docker/compose/releases/download/$compose_version/$asset.sha256" -o "$download/$asset.sha256"
    (cd "$download" && sha256sum --check "$asset.sha256")
    install -m 0755 "$download/$asset" "$plugin_dir/docker-compose"
fi
docker compose up --help | grep -q -- '--wait' || die 'Docker Compose with up --wait support is required (2.20+).'

staging=$(mktemp -d)
trap 'rm -rf -- "$staging"; if [[ -n ${download:-} ]]; then rm -rf -- "$download"; fi' EXIT
git clone --branch "$RELEASE" --depth 1 "$REPOSITORY" "$staging/source"
cd "$staging/source"
source scripts/install-lib.sh
printf '\n1) Automatic HTTPS (public DNS domain, free TCP 80 and chosen HTTPS port)\n2) Existing reverse proxy on this host (loopback backend; configure your proxy separately)\n'
while :; do
    ask mode 'Mode' 1
    [[ "$mode" == 1 || "$mode" == 2 ]] && break
done
while :; do
    ask domain 'Panel DNS hostname (no scheme, port or path)'
    valid_domain "$domain" && break
    printf 'Enter a valid DNS hostname, e.g. desk.example.com.\n'
done
if [[ "$mode" == 1 ]]; then
    port_available 80 || fail 'TCP 80 is occupied. Run the installer again and choose existing reverse proxy mode.'
    getent ahosts "$domain" >/dev/null || fail 'Domain does not resolve. Set DNS first, then run the installer again.'
    while :; do
        ask_port https_port 'Public HTTPS port (not 80)' 443
        [[ "$https_port" != 80 ]] && break
    done
    while :; do
        ask email 'Email for TLS certificate notices'
        [[ "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]] && break
    done
    printf 'DNS A/AAAA must point here. Allow inbound TCP 80 and %s in your provider firewall/router.\n' "$https_port"
    ask ready 'DNS and external firewall ready? (yes/no)' no
    [[ "$ready" == yes ]] || fail 'Prepare DNS/firewall, then run the installer again.'
    files=compose.yaml:compose.https.yaml
else
    while :; do
        ask https_port 'HTTPS port on your existing reverse proxy' 443
        valid_port "$https_port" && break
    done
    while :; do
        ask_port proxy_port 'Local backend port for your reverse proxy' 18080
        [[ "$proxy_port" != "$https_port" ]] && break
        printf 'The backend port must differ from the public HTTPS port.\n'
    done
    files=compose.yaml:compose.proxy.yaml
fi
origin="https://$domain"
[[ "$https_port" == 443 ]] || origin+=":$https_port"
mv -- "$staging/source" "$DEPLOY"
cd "$DEPLOY"
install -d -m 0700 -o 10001 -g 10001 "$DATA"
cat > .env <<EOF
COMPOSE_FILE=$files
BAMDAD_ORIGIN=$origin
BAMDAD_DOMAIN=$domain
BAMDAD_DATA_DIR=$DATA
BAMDAD_HTTPS_PORT=$https_port
BAMDAD_PROXY_PORT=${proxy_port:-18080}
BAMDAD_TLS_EMAIL=${email:-}
EOF
chmod 0600 .env
printf '\nBuilding panel and creating the first administrator...\n'
bash manage.sh resume
if [[ "$mode" == 2 ]]; then
    printf '\nProxy HTTPS %s to http://127.0.0.1:%s (see docs/INSTALL.md).\n' "$origin" "$proxy_port"
fi
printf '\nChecking public HTTPS endpoint...\n'
if health=$(curl --proto '=https' --tlsv1.2 -fsS --retry 8 --retry-all-errors --retry-delay 5 --max-time 10 "$origin/healthz") && [[ "$health" == '{"status":"ok"}' ]]; then
    printf '\nPanel is reachable: %s\n' "$origin"
else
    printf '\nContainers are running, but public HTTPS is not verified. Check DNS, certificates, firewall/proxy and run: sudo bash %s/manage.sh status\n' "$DEPLOY" >&2
    exit 1
fi
