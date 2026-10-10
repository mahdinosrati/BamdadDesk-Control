#!/usr/bin/env bash

fail() { printf 'Error: %s\n' "$*" >&2; exit 1; }
ask() {
    local answer
    read -r -p "$2${3:+ [$3]}: " answer </dev/tty
    printf -v "$1" '%s' "${answer:-${3:-}}"
}
valid_port() { [[ "$1" =~ ^[1-9][0-9]{0,4}$ ]] && ((10#$1 <= 65535)); }
valid_ipv4() {
    local octet
    local -a octets
    [[ "$1" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]] || return 1
    IFS=. read -ra octets <<< "$1"
    for octet in "${octets[@]}"; do
        [[ "$octet" =~ ^(0|[1-9][0-9]{0,2})$ ]] && ((10#$octet <= 255)) || return 1
    done
}
valid_host() { valid_ipv4 "$1" || valid_domain "$1"; }
valid_domain() {
    [[ ${#1} -le 253 && "$1" == *.* && "$1" != *..* && "$1" != *[!a-zA-Z0-9.-]* ]] || return 1
    local label
    local -a labels
    IFS=. read -ra labels <<< "$1"
    for label in "${labels[@]}"; do
        [[ ${#label} -le 63 && "$label" =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$ ]] || return 1
    done
    [[ "$1" != *. && "$1" =~ [a-zA-Z] ]]
}
port_available() {
    local listeners published
    if [[ ${BAMDAD_RECONFIGURE:-0} == 1 ]]; then
        published=$(docker ps --filter label=com.docker.compose.project=bamdaddesk-control --format '{{.Ports}}') || return 1
        if grep -Eq ":${1}->" <<< "$published"; then return 0; fi
    fi
    listeners=$(ss -H -ltn "sport = :$1") || return 1
    [[ -z "$listeners" ]] || return 1
    # Docker may publish ports with NAT and no listening userspace socket.
    published=$(docker ps --format '{{.Ports}}') || return 1
    ! grep -Eq ":${1}->" <<< "$published"
}
ask_port() {
    local chosen
    while :; do
        ask chosen "$2" "$3"
        if valid_port "$chosen" && port_available "$chosen"; then
            printf -v "$1" '%s' "$chosen"
            return
        fi
        printf 'Choose an unused TCP port between 1 and 65535.\n'
    done
}
