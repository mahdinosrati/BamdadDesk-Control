#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

readonly REPOSITORY=https://github.com/mahdinosrati/BamdadDesk-Control.git
readonly RELEASE=v1.2.0
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
    if [[ -f "$DEPLOY/scripts/show-url.sh" ]]; then bash "$DEPLOY/scripts/show-url.sh"; elif [[ -f "$DEPLOY/.env" ]]; then grep "^BAMDAD_ORIGIN=" "$DEPLOY/.env"; fi
    die "Deployment already exists. Upgrade to $RELEASE then run sudo bash $DEPLOY/manage.sh configure; see docs/OPERATIONS.md. For a configured deployment run: sudo bash $DEPLOY/manage.sh resume. See docs/OPERATIONS.md for incomplete setup recovery."
fi
[[ ! -e "$DATA" ]] || die "$DATA already exists; refusing to overwrite existing data."

printf 'Installing BamdadDesk Control %s. Existing RustDesk services will remain running.\n' "$RELEASE"
printf 'Created by Mahdi Nosrati / مهدی نصرتی — mahdinosrati06@gmail.com — https://t.me/MiNosrati\n'
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
bash scripts/configure.sh
mv -- "$staging/source" "$DEPLOY"
cd "$DEPLOY"
install -d -m 0700 -o 10001 -g 10001 "$DATA"
# Print the configured URL on success or failure, including interrupted bootstrap.
result=0
trap 'result=$?; bash "$DEPLOY/scripts/show-url.sh"; rm -rf -- "$staging"; if [[ -n ${download:-} ]]; then rm -rf -- "$download"; fi; exit "$result"' EXIT
printf '\nBuilding panel and creating the first administrator...\n'
bash manage.sh resume
origin=$(sed -n 's/^BAMDAD_ORIGIN=//p' .env)
printf '\nChecking configured endpoint: %s\n' "$origin"
if health=$(curl --proto '=http,https' -fsS --retry 3 --retry-all-errors --retry-delay 3 --connect-timeout 5 --max-time 10 "$origin/healthz") && [[ "$health" == '{"status":"ok"}' ]]; then
    printf '\nPanel is reachable: %s\n' "$origin"
else
    printf '\nAPI started, but the public URL is not verified. Check firewall, DNS or proxy routing.\n' >&2
    exit 1
fi
printf '\nOptional: install a new RustDesk OSS server alongside the panel. Choose no if you already have one.\n'
read -r -p 'Install bundled RustDesk server? (yes/no) [no]: ' bundled </dev/tty
if [[ "$bundled" == yes ]]; then bash scripts/rustdesk.sh install; fi
if [[ ! -e /usr/local/bin/bamdad ]]; then
    printf '#!/usr/bin/env bash\nexec bash /opt/bamdaddesk-control/manage.sh "$@"\n' > /usr/local/bin/bamdad
    chmod 0755 /usr/local/bin/bamdad
fi
printf '\nManagement menu: sudo bash %s/manage.sh\n' "$DEPLOY"
