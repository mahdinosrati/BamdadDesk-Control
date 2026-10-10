#!/usr/bin/env bash
set -Eeuo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
if [[ -f .env ]]; then
    origin=$(sed -n 's/^BAMDAD_ORIGIN=//p' .env | head -n 1)
    printf '\nPanel URL: %s\n' "${origin:-Not configured}"
    printf 'Status: sudo bash %s/manage.sh status\n' "$PWD"
    printf 'Logs: sudo bash %s/manage.sh logs\n' "$PWD"
fi
