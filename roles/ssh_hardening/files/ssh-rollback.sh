#!/usr/bin/env bash
set -euo pipefail

BACKUP_FILE="/var/lib/ssh-hardening/00-hardening.conf.good"
CONFIG_FILE="/etc/ssh/sshd_config.d/00-hardening.conf"

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "ERROR: Backup not found" >&2
    exit 1
else
cp -p "$BACKUP_FILE" "$CONFIG_FILE"
/usr/sbin/sshd -t -f /etc/ssh/sshd_config
systemctl reload sshd
fi
