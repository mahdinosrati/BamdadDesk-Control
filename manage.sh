#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
[[ $EUID -eq 0 ]] || { echo 'Run with sudo'; exit 1; }
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ -f .env ]] || { echo 'Missing .env; see docs/OPERATIONS.md'; exit 1; }
trap 'bash scripts/show-url.sh' EXIT
case "${1:-menu}" in
    menu) bash scripts/menu.sh ;;
    rustdesk) bash scripts/rustdesk.sh "${2:-status}" ;;
    tls)
        origin=$(sed -n 's/^BAMDAD_ORIGIN=//p' .env)
        [[ "$origin" == https://* ]] || { echo 'HTTPS is disabled. Run manage.sh configure and select automatic HTTPS.'; exit 1; }
        printf 'Caddy automatically issues and renews managed certificates. Public endpoint: %s\n' "$origin"
        curl --proto '=https' --connect-timeout 10 --max-time 20 -Iv "$origin/healthz"
        ;;
    update)
        tag=${2:-}
        [[ "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$ ]] || { echo 'Provide an explicit release tag, for example: manage.sh update v1.2.0'; exit 1; }
        [[ -z $(git status --porcelain --untracked-files=no) ]] || { echo 'Tracked files were modified; save/review local changes before upgrading.'; exit 1; }
        git fetch origin "refs/tags/$tag:refs/tags/$tag"
        bash manage.sh backup /var/backups/bamdaddesk-control
        git checkout --detach "$tag"
        bash manage.sh resume
        ;;
    uninstall)
        [[ "$PWD" == /opt/bamdaddesk-control && ! -L /opt/bamdaddesk-control ]] || { echo 'Automatic uninstall only supports /opt/bamdaddesk-control.'; exit 1; }
        data_dir=$(sed -n 's/^BAMDAD_DATA_DIR=//p' .env)
        [[ "$data_dir" == /var/lib/bamdaddesk-control && ! -L "$data_dir" ]] || { echo 'Custom data directory: use the documented manual removal procedure.'; exit 1; }
        printf 'This deletes panel accounts, devices, releases, signing key and TLS volumes. Backups and the optional RustDesk server are retained.\n'
        read -r -p 'Type DELETE PANEL DATA to confirm: ' confirmation </dev/tty
        [[ "$confirmation" == 'DELETE PANEL DATA' ]] || { echo 'Cancelled'; exit 1; }
        docker compose down --volumes
        trap - EXIT
        cd /opt
        rm -rf -- /var/lib/bamdaddesk-control /opt/bamdaddesk-control
        if [[ -f /usr/local/bin/bamdad ]] && grep -Fqx 'exec bash /opt/bamdaddesk-control/manage.sh "$@"' /usr/local/bin/bamdad; then rm -- /usr/local/bin/bamdad; fi
        printf 'Panel removed. Docker, backups and RustDesk were retained.\n'
        ;;
    configure)
        bash scripts/configure.sh
        bash manage.sh resume
        ;;
    resume)
        if docker buildx version >/dev/null 2>&1; then
            docker build --tag bamdaddesk-control:local .
        else
            DOCKER_BUILDKIT=0 docker build --tag bamdaddesk-control:local .
        fi
        printf '\nCreate the panel administrator below. Password input is hidden.\n'
        docker compose run --rm --no-deps --interactive --tty api python -m control.bootstrap </dev/tty >/dev/tty 2>/dev/tty
        docker compose up -d --no-build --remove-orphans --wait --wait-timeout 120
        ;;
    status) docker compose ps ;;
    logs) docker compose logs --tail 100 "${2:-api}" ;;
    backup)
        [[ ${2:-} == /* ]] || { echo 'Usage: manage.sh backup /absolute/backup/directory'; exit 1; }
        install -d -m 0700 "$2"
        destination=$(realpath "$2")
        case "$destination/" in /var/lib/bamdaddesk-control/*) echo 'Backup must be outside the data directory'; exit 1 ;; esac
        archive="$destination/bamdad-$(date -u +%Y%m%dT%H%M%SZ).tar.gz"
        [[ ! -e "$archive" ]] || { echo 'Backup already exists'; exit 1; }
        docker compose ps --status running --services | grep -qx api || { echo 'API must be running before this online backup'; exit 1; }
        docker compose stop api
        trap 'docker compose start api >/dev/null' EXIT
        tar -czf "$archive" -C /var/lib bamdaddesk-control -C "$PWD" .env Caddyfile
        (cd "$destination" && sha256sum "$(basename "$archive")" > "$(basename "$archive").sha256")
        printf 'Backup: %s\nSource commit: ' "$archive"
        git rev-parse HEAD | tee "$archive.commit"
        ;;
    *) echo 'Usage: manage.sh {menu|configure|resume|status|tls|update TAG|uninstall|rustdesk ACTION|logs [api|caddy]|backup /absolute/directory}'; exit 1 ;;
esac
