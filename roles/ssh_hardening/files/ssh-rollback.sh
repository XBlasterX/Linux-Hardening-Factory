#!/usr/bin/env bash
set -euo pipefail

BACKUP_FILE="/var/lib/ssh-hardening/00-hardening.conf.good"
CONFIG_FILE="/etc/ssh/sshd_config.d/00-hardening.conf"

if [[ -f "$BACKUP_FILE" ]]; then
    cp -p "$BACKUP_FILE" "$CONFIG_FILE"
else
    # If no previous configuration existed, remove the invalid drop-in
    rm -f "$CONFIG_FILE"
fi

/usr/sbin/sshd -t -f /etc/ssh/sshd_config
systemctl reload sshd
