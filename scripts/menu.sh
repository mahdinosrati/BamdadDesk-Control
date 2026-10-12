#!/usr/bin/env bash
set -Eeuo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
source scripts/install-lib.sh
while :; do
    printf '\nBamdadDesk Control — Created by Mahdi Nosrati / مهدی نصرتی\n'
    printf '1) Status and panel URL\n2) Change panel address / port / HTTPS mode\n3) Update panel (with backup)\n4) Backup panel\n5) RustDesk server management\n6) Free SSL and certificate status\n7) Uninstall panel\n0) Exit\n'
    choice='';ask choice 'Choice' 1
    case "$choice" in
        1) bash manage.sh status ;;
        2) bash manage.sh configure ;;
        3) tag='';ask tag 'Published release tag';bash manage.sh update "$tag" ;;
        4) bash manage.sh backup /var/backups/bamdaddesk-control ;;
        5)
            printf 'Actions: install, configure, status, logs, start, stop, restart, key, backup, update\n'
            action='';ask action 'RustDesk action' status
            bash manage.sh rustdesk "$action"
            ;;
        6)
            printf '1) Configure free automatic HTTPS\n2) Show certificate status\n3) Show TLS renewal logs\n'
            action='';ask action 'TLS action' 2
            case "$action" in 1) bash manage.sh configure ;; 2) bash manage.sh tls ;; 3) bash manage.sh logs caddy ;; *) printf 'Unknown action\n' ;; esac
            ;;
        7) bash manage.sh uninstall; exit ;;
        0) exit ;;
        *) printf 'Unknown choice\n' ;;
    esac
done
