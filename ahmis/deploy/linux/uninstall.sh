#!/usr/bin/env bash
# AHMIS – désinstallation Linux.  sudo bash uninstall.sh [--purge]
#   --purge : supprime aussi les données (/var/lib/ahmis) et la configuration (/etc/ahmis)
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "Lancez en root."; exit 1; }
PURGE=0; [ "${1:-}" = "--purge" ] && PURGE=1
systemctl disable --now ahmis ahmis-backup.timer 2>/dev/null || true
rm -f /etc/systemd/system/ahmis.service /etc/systemd/system/ahmis-backup.service /etc/systemd/system/ahmis-backup.timer
systemctl daemon-reload
rm -f /etc/nginx/sites-enabled/ahmis /etc/nginx/sites-available/ahmis /etc/nginx/conf.d/ahmis.conf
[ -f /etc/nginx/nginx.conf.avant-ahmis ] && mv -f /etc/nginx/nginx.conf.avant-ahmis /etc/nginx/nginx.conf
command -v nginx >/dev/null && nginx -t 2>/dev/null && systemctl reload nginx 2>/dev/null || true
rm -rf /opt/ahmis /usr/local/bin/ahmis-manage
if [ "$PURGE" = 1 ]; then
  rm -rf /var/lib/ahmis /etc/ahmis
  userdel ahmis 2>/dev/null || true
  echo "AHMIS désinstallé, données et configuration supprimées."
else
  echo "AHMIS désinstallé. Données conservées dans /var/lib/ahmis et configuration dans /etc/ahmis."
fi
