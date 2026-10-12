#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
source scripts/install-lib.sh
[[ $EUID -eq 0 ]] || fail 'Run with sudo.'
readonly server_dir=/var/lib/bamdaddesk-rustdesk
server_compose() { docker compose --env-file "$server_dir/server.env" -f "$PWD/compose.rustdesk.yaml" "$@"; }
configure_server() {
    local server_host id_port relay_port
    server_host='' id_port='' relay_port=''
    printf 'Use an external/existing RustDesk server by keeping this optional component uninstalled.\n'
    while :; do ask server_host 'Public RustDesk hostname or IPv4'; valid_host "$server_host" && break; done
    while :; do
        ask id_port 'ID port (also reserves the preceding TCP port)' 21116
        valid_port "$id_port" && ((id_port > 1)) && break
    done
    while :; do
        ask relay_port 'Relay TCP port' 21117
        valid_port "$relay_port" && [[ "$relay_port" != "$id_port" && "$relay_port" != "$((id_port-1))" ]] && break
    done
    if [[ ! -f "$server_dir/server.env" ]]; then
        for port in "$id_port" "$((id_port-1))" "$relay_port"; do
            port_available "$port" || fail "TCP port $port is occupied; retain the existing server or choose other ports."
        done
        [[ -z $(ss -H -lun "sport = :$id_port") ]] || fail "UDP port $id_port is occupied."
    fi
    install -d -m 0700 "$server_dir" "$server_dir/data"
    [[ ! -f "$server_dir/server.env" ]] || cp -p "$server_dir/server.env" "$server_dir/server.env.backup.$(date -u +%Y%m%dT%H%M%S%N)"
    cat > "$server_dir/server.env" <<EOF
RUSTDESK_VERSION=1.1.16
RUSTDESK_HOST=$server_host
RUSTDESK_ID_PORT=$id_port
RUSTDESK_NAT_PORT=$((id_port-1))
RUSTDESK_RELAY_PORT=$relay_port
EOF
    server_compose up -d
    printf 'Allow TCP %s,%s,%s and UDP %s in the external firewall.\n' "$((id_port-1))" "$id_port" "$relay_port" "$id_port"
    printf 'Set panel Global access policy: ID server %s:%s, relay %s:%s. Obtain its key with: manage.sh rustdesk key\n' "$server_host" "$id_port" "$server_host" "$relay_port"
}
case "${1:-status}" in
    configure|install) configure_server ;;
    status|logs|start|stop|restart|key|backup|update)
        [[ -f "$server_dir/server.env" ]] || fail 'Optional RustDesk server is not installed by this project.'
        case "$1" in
            status) server_compose ps ;;
            logs) server_compose logs --tail 100 ;;
            start) server_compose up -d ;;
            stop|restart) server_compose "$1" ;;
            key) cat "$server_dir/data/id_ed25519.pub" ;;
            backup)
                install -d -m 0700 /var/backups/bamdaddesk-control
                archive="/var/backups/bamdaddesk-control/rustdesk-$(date -u +%Y%m%dT%H%M%S%N).tar.gz"
                server_compose stop
                trap 'server_compose start' EXIT
                tar -czf "$archive" -C /var/lib bamdaddesk-rustdesk
                sha256sum "$archive" > "$archive.sha256"
                printf 'Private keys and server data saved to %s\n' "$archive"
                ;;
            update)
                version='';ask version 'Explicit upstream Docker image version' 1.1.16
                [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail 'Expected a numeric release version.'
                bash scripts/rustdesk.sh backup
                cp -p "$server_dir/server.env" "$server_dir/server.env.before-update"
                sed -i "s/^RUSTDESK_VERSION=.*/RUSTDESK_VERSION=$version/" "$server_dir/server.env"
                server_compose pull
                server_compose up -d
                ;;
        esac
        ;;
    *) fail 'Usage: manage.sh rustdesk {install|configure|status|logs|start|stop|restart|key|backup|update}' ;;
esac
