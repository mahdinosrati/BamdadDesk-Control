#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
[[ $EUID -eq 0 ]] || { echo 'Run with sudo'; exit 1; }
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
[[ -f .env ]] || { echo 'Missing .env; see docs/OPERATIONS.md'; exit 1; }
case "${1:-status}" in
    resume)
        if docker buildx version >/dev/null 2>&1; then
            docker build --tag bamdaddesk-control:local .
        else
            DOCKER_BUILDKIT=0 docker build --tag bamdaddesk-control:local .
        fi
        docker compose run --rm --no-deps api python -m control.bootstrap </dev/tty
        docker compose up -d --no-build --wait --wait-timeout 120
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
    *) echo 'Usage: manage.sh {resume|status|logs [api|caddy]|backup /absolute/directory}'; exit 1 ;;
esac
