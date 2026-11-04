#!/usr/bin/env bash
# ============================================================================
#  AHMIS – installation serveur Linux
#  Distributions : Debian 12+, Ubuntu 22.04+, RHEL / Rocky / Alma 9+
#
#  Usage (en root, depuis le dossier AHMIS décompressé) :
#     sudo bash deploy/linux/install.sh [options]
#
#  Options :
#     --demo                 charge les données de démonstration (comptes démo affichés)
#     --admin-password XXX   mot de passe du compte « admin » (sinon généré et affiché)
#     --port 80              port HTTP public (défaut 80 avec nginx, 8000 sans)
#     --no-nginx             pas de nginx : gunicorn écoute directement sur le port public
#     --server-name NOM      nom DNS d'accès (ajouté aux hôtes autorisés)
#     --url-prefix /ahmis    publie AHMIS sous un sous-chemin d'un site nginx existant
#     --nginx-include-into F avec --url-prefix : fichier « server » nginx existant où ajouter
#                            les emplacements AHMIS (le reste du site n'est pas modifié)
#     --dnf-repos R1,R2      dnf : dépôts à utiliser seuls (petites VM à faible mémoire)
#
#  Relancer le script avec une version plus récente d'AHMIS = mise à jour
#  (le code est remplacé ; la configuration et les données sont conservées).
# ============================================================================
set -euo pipefail

APP_DIR=/opt/ahmis
ETC_DIR=/etc/ahmis
DATA_DIR=/var/lib/ahmis
ENV_FILE=$ETC_DIR/ahmis.env
SVC_USER=ahmis
SRC_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

DEMO=0; ADMIN_PW=""; USE_NGINX=1; PORT=""; SERVER_NAME=""; URL_PREFIX=""; NGINX_INCLUDE_INTO=""; DNF_REPOS=""
while [ $# -gt 0 ]; do
  case "$1" in
    --demo) DEMO=1 ;;
    --admin-password) ADMIN_PW="$2"; shift ;;
    --no-nginx) USE_NGINX=0 ;;
    --port) PORT="$2"; shift ;;
    --server-name) SERVER_NAME="$2"; shift ;;
    --url-prefix) URL_PREFIX="/$(echo "$2" | sed 's#^/*##; s#/*$##')"; shift ;;
    --nginx-include-into) NGINX_INCLUDE_INTO="$2"; shift ;;
    --dnf-repos) DNF_REPOS="$2"; shift ;;
    -h|--help) sed -n 2,20p "$0"; exit 0 ;;
    *) echo "Option inconnue : $1"; exit 2 ;;
  esac
  shift
done
[ -z "$PORT" ] && { [ "$USE_NGINX" = 1 ] && PORT=80 || PORT=8000; }

say()  { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m[!] %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m[ERREUR] %s\033[0m\n' "$*"; exit 1; }

[ "$(id -u)" = 0 ] || die "Lancez ce script en root : sudo bash deploy/linux/install.sh"
[ -f "$SRC_DIR/manage.py" ] || die "manage.py introuvable dans $SRC_DIR : lancez le script depuis le dossier AHMIS décompressé."
command -v systemctl >/dev/null || die "systemd est requis."

# ---------------------------------------------------------------- paquets système
say "Installation des paquets système"
if command -v apt-get >/dev/null; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq python3 python3-venv python3-pip sqlite3 ca-certificates >/dev/null
  [ "$USE_NGINX" = 1 ] && apt-get install -y -qq nginx >/dev/null
  PKG=apt
elif command -v dnf >/dev/null; then
  DNF=(dnf install -y -q)
  [ -n "$DNF_REPOS" ] && DNF+=(--disablerepo="*" --enablerepo="$DNF_REPOS")
  "${DNF[@]}" python3 sqlite ca-certificates >/dev/null
  [ "$USE_NGINX" = 1 ] && { command -v nginx >/dev/null || "${DNF[@]}" nginx >/dev/null; }
  PKG=dnf
else
  die "Gestionnaire de paquets non pris en charge (apt ou dnf requis)."
fi

# Python 3.10+ (RHEL 9 fournit 3.9 par défaut : on installe python3.11/3.12)
find_python() {
  for c in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v "$c" >/dev/null && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
      command -v "$c"; return 0
    fi
  done
  return 1
}
PY="$(find_python || true)"
if [ -z "$PY" ] && [ "$PKG" = dnf ]; then
  "${DNF[@]}" python3.12 python3.12-pip >/dev/null 2>&1 || "${DNF[@]}" python3.11 >/dev/null 2>&1 || true
  PY="$(find_python || true)"
fi
[ -n "$PY" ] || die "Python 3.10 ou plus récent introuvable. Installez-le puis relancez."
echo "Python : $($PY --version) ($PY)"

# ---------------------------------------------------------------- utilisateur et dossiers
say "Compte de service et dossiers"
id "$SVC_USER" >/dev/null 2>&1 || useradd --system --home-dir "$DATA_DIR" --shell /usr/sbin/nologin "$SVC_USER"
install -d -m 0755 "$APP_DIR"
install -d -m 0750 -o root -g "$SVC_USER" "$ETC_DIR"
install -d -m 0750 -o "$SVC_USER" -g "$SVC_USER" "$DATA_DIR" "$DATA_DIR/db" "$DATA_DIR/media" "$DATA_DIR/logs" "$DATA_DIR/backups"

# ---------------------------------------------------------------- code de l'application
say "Copie de l'application dans $APP_DIR"
if [ "$SRC_DIR" != "$APP_DIR" ]; then
  # Mise à jour : l'ancien code est remplacé (l'environnement Python est conservé)
  find "$APP_DIR" -mindepth 1 -maxdepth 1 ! -name .venv -exec rm -rf {} +
  tar -C "$SRC_DIR" --exclude=.venv --exclude=db --exclude=media --exclude=staticfiles --exclude='__pycache__' \
      --exclude=ahmis.env --exclude=wheels -cf - . | tar -C "$APP_DIR" -xf -
fi
chown -R root:root "$APP_DIR"

# ---------------------------------------------------------------- environnement Python
say "Environnement Python et dépendances"
if [ -x "$APP_DIR/.venv/bin/python" ] && ! "$APP_DIR/.venv/bin/python" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)'; then
  rm -rf "$APP_DIR/.venv"
fi
[ -x "$APP_DIR/.venv/bin/python" ] || "$PY" -m venv "$APP_DIR/.venv"
PIP_OPTS=(--disable-pip-version-check -q)
if [ -d "$SRC_DIR/wheels" ]; then
  echo "Installation hors ligne depuis $SRC_DIR/wheels"
  PIP_OPTS+=(--no-index --find-links "$SRC_DIR/wheels")
else
  "$APP_DIR/.venv/bin/pip" install "${PIP_OPTS[@]}" --upgrade pip
fi
"$APP_DIR/.venv/bin/pip" install "${PIP_OPTS[@]}" -r "$APP_DIR/requirements-server.txt"

# ---------------------------------------------------------------- configuration
say "Configuration ($ENV_FILE)"
if [ ! -f "$ENV_FILE" ]; then
  SECRET="$("$APP_DIR/.venv/bin/python" -c 'import secrets; print(secrets.token_urlsafe(64))')"
  HOSTS="localhost,127.0.0.1,$(hostname)"
  FQDN="$(hostname -f 2>/dev/null || true)"; [ -n "$FQDN" ] && [ "$FQDN" != "$(hostname)" ] && HOSTS="$HOSTS,$FQDN"
  for ip in $(hostname -I 2>/dev/null || true); do case "$ip" in *:*) ;; *) HOSTS="$HOSTS,$ip" ;; esac; done
  [ -n "$SERVER_NAME" ] && HOSTS="$HOSTS,$SERVER_NAME"
  ORIGINS=""
  IFS=',' read -ra H <<< "$HOSTS"
  for h in "${H[@]}"; do
    if [ "$PORT" = 80 ]; then ORIGINS="$ORIGINS,http://$h"; else ORIGINS="$ORIGINS,http://$h:$PORT"; fi
  done
  if [ "$USE_NGINX" = 1 ]; then BIND="127.0.0.1:8001"; else BIND="0.0.0.0:$PORT"; fi
  sed -e "s|^AHMIS_SECRET_KEY=.*|AHMIS_SECRET_KEY=$SECRET|" \
      -e "s|^AHMIS_ALLOWED_HOSTS=.*|AHMIS_ALLOWED_HOSTS=$HOSTS|" \
      -e "s|^AHMIS_CSRF_TRUSTED_ORIGINS=.*|AHMIS_CSRF_TRUSTED_ORIGINS=${ORIGINS#,}|" \
      -e "s|^AHMIS_DATA_DIR=.*|AHMIS_DATA_DIR=$DATA_DIR|" \
      -e "s|^AHMIS_BIND=.*|AHMIS_BIND=$BIND|" \
      -e "s|^AHMIS_DEMO=.*|AHMIS_DEMO=$DEMO|" \
      "$APP_DIR/deploy/ahmis.env.exemple" > "$ENV_FILE"
  echo "AHMIS_STATIC_ROOT=$APP_DIR/staticfiles" >> "$ENV_FILE"
  [ -n "$URL_PREFIX" ] && echo "AHMIS_URL_PREFIX=$URL_PREFIX" >> "$ENV_FILE"
  chown root:"$SVC_USER" "$ENV_FILE"; chmod 0640 "$ENV_FILE"
  echo "Fichier de configuration créé."
else
  echo "Configuration existante conservée."
fi
BIND="$(grep -E '^AHMIS_BIND=' "$ENV_FILE" | cut -d= -f2-)"

# Commande d'administration : ahmis-manage <commande> (exécutée avec le compte de service)
cat > /usr/local/bin/ahmis-manage <<EOF
#!/usr/bin/env bash
cd $APP_DIR
exec sudo -u $SVC_USER env AHMIS_ENV_FILE=$ENV_FILE $APP_DIR/.venv/bin/python $APP_DIR/manage.py "\$@"
EOF
chmod 0755 /usr/local/bin/ahmis-manage
command -v sudo >/dev/null || die "sudo est requis pour ahmis-manage (apt/dnf install sudo)."

# ---------------------------------------------------------------- base de données
say "Base de données et fichiers statiques"
install -d -m 0755 "$APP_DIR/staticfiles"
AHMIS_ENV_FILE=$ENV_FILE "$APP_DIR/.venv/bin/python" "$APP_DIR/manage.py" collectstatic --noinput -v0
chown -R "$SVC_USER:$SVC_USER" "$DATA_DIR"   # journaux éventuellement créés par root ci-dessus
ahmis-manage migrate --noinput -v1
if [ "$DEMO" = 1 ]; then
  ahmis-manage load_demo
else
  if [ -z "$ADMIN_PW" ] && ! ahmis-manage shell -c "from django.contrib.auth import get_user_model as g; import sys; sys.exit(0 if g().objects.filter(username='admin').exists() else 1)" 2>/dev/null; then
    ADMIN_PW="$("$APP_DIR/.venv/bin/python" -c 'import secrets; print(secrets.token_urlsafe(12))')"
    GENERATED_PW=1
  fi
  AHMIS_ADMIN_PASSWORD="$ADMIN_PW" sudo -u "$SVC_USER" env AHMIS_ENV_FILE="$ENV_FILE" AHMIS_ADMIN_PASSWORD="$ADMIN_PW" \
    "$APP_DIR/.venv/bin/python" "$APP_DIR/manage.py" ahmis_init
fi

# ---------------------------------------------------------------- service systemd
say "Service systemd « ahmis »"
cat > /etc/systemd/system/ahmis.service <<EOF
[Unit]
Description=AHMIS - Maintenance Information System
After=network-online.target
Wants=network-online.target

[Service]
User=$SVC_USER
Group=$SVC_USER
WorkingDirectory=$APP_DIR
Environment=AHMIS_ENV_FILE=$ENV_FILE
ExecStart=$APP_DIR/.venv/bin/gunicorn config.wsgi:application --bind $BIND --workers 2 --threads 4 --worker-class gthread --timeout 120 --access-logfile $DATA_DIR/logs/access.log --error-logfile $DATA_DIR/logs/gunicorn.log
Restart=always
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$DATA_DIR
$( [ "$USE_NGINX" = 0 ] && [ "${PORT}" -lt 1024 ] && echo "AmbientCapabilities=CAP_NET_BIND_SERVICE" )

[Install]
WantedBy=multi-user.target
EOF

# Sauvegarde quotidienne (02:30), 30 sauvegardes conservées
cat > /etc/systemd/system/ahmis-backup.service <<EOF
[Unit]
Description=AHMIS - sauvegarde quotidienne
[Service]
Type=oneshot
User=$SVC_USER
WorkingDirectory=$APP_DIR
Environment=AHMIS_ENV_FILE=$ENV_FILE
ExecStart=$APP_DIR/.venv/bin/python $APP_DIR/manage.py ahmis_backup --keep 30
EOF
cat > /etc/systemd/system/ahmis-backup.timer <<EOF
[Unit]
Description=AHMIS - sauvegarde quotidienne
[Timer]
OnCalendar=*-*-* 02:30:00
Persistent=true
[Install]
WantedBy=timers.target
EOF
systemctl daemon-reload
systemctl enable --now ahmis-backup.timer >/dev/null
systemctl enable ahmis >/dev/null
systemctl restart ahmis

# ---------------------------------------------------------------- nginx
if [ "$USE_NGINX" = 1 ] && [ -n "$URL_PREFIX" ]; then
  say "nginx : AHMIS publié sous $URL_PREFIX/"
  [ -n "$NGINX_INCLUDE_INTO" ] || die "--url-prefix demande --nginx-include-into <fichier du site nginx existant>."
  [ -f "$NGINX_INCLUDE_INTO" ] || die "Fichier nginx introuvable : $NGINX_INCLUDE_INTO"
  cat > /etc/nginx/ahmis-locations.conf <<NGX
# AHMIS (généré par deploy/linux/install.sh) : inclus dans le site existant
location = $URL_PREFIX { return 301 $URL_PREFIX/; }
location $URL_PREFIX/static/ {
    alias $APP_DIR/staticfiles/;
    expires 7d;
    access_log off;
}
location $URL_PREFIX/ {
    client_max_body_size 25m;
    proxy_pass http://$BIND/;
    proxy_set_header Host \$host;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_read_timeout 120s;
}
NGX
  if ! grep -q "ahmis-locations.conf" "$NGINX_INCLUDE_INTO"; then
    cp -n "$NGINX_INCLUDE_INTO" "$NGINX_INCLUDE_INTO.avant-ahmis"
    # Ajout juste après la première ligne « server { » (le reste du site est inchangé)
    sed -i '0,/server[[:space:]]*{/s//&\n    include \/etc\/nginx\/ahmis-locations.conf;/' "$NGINX_INCLUDE_INTO"
  fi
  if command -v getenforce >/dev/null && [ "$(getenforce)" != Disabled ]; then
    setsebool -P httpd_can_network_connect 1 2>/dev/null || true
    chcon -R -t httpd_sys_content_t "$APP_DIR/staticfiles" 2>/dev/null || true
  fi
  if ! nginx -t; then
    cp "$NGINX_INCLUDE_INTO.avant-ahmis" "$NGINX_INCLUDE_INTO"
    rm -f /etc/nginx/ahmis-locations.conf
    die "Configuration nginx refusée : fichier d'origine restauré."
  fi
  systemctl reload nginx
elif [ "$USE_NGINX" = 1 ]; then
  say "Serveur web nginx (port $PORT)"
  NGINX_CONF="server {
    listen $PORT default_server;
    listen [::]:$PORT default_server;
    server_name _;
    client_max_body_size 25m;
    server_tokens off;
    add_header X-Content-Type-Options nosniff;

    location /static/ {
        alias $APP_DIR/staticfiles/;
        expires 7d;
        access_log off;
    }
    location / {
        proxy_pass http://$BIND;
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
    }
}"
  if [ -d /etc/nginx/sites-available ]; then
    echo "$NGINX_CONF" > /etc/nginx/sites-available/ahmis
    ln -sf /etc/nginx/sites-available/ahmis /etc/nginx/sites-enabled/ahmis
    rm -f /etc/nginx/sites-enabled/default
  else
    echo "$NGINX_CONF" > /etc/nginx/conf.d/ahmis.conf
    # RHEL : le serveur par défaut de nginx.conf occupe aussi le port 80
    if grep -q "default_server" /etc/nginx/nginx.conf; then
      cp -n /etc/nginx/nginx.conf /etc/nginx/nginx.conf.avant-ahmis
      sed -i 's/ default_server//g' /etc/nginx/nginx.conf
    fi
  fi
  if command -v getenforce >/dev/null && [ "$(getenforce)" != Disabled ]; then
    setsebool -P httpd_can_network_connect 1 2>/dev/null || true
    chcon -R -t httpd_sys_content_t "$APP_DIR/staticfiles" 2>/dev/null || true
  fi
  nginx -t
  systemctl enable nginx >/dev/null
  systemctl restart nginx
fi

# ---------------------------------------------------------------- pare-feu
if [ -n "$URL_PREFIX" ]; then
  :  # site existant : ports déjà ouverts
elif command -v ufw >/dev/null && ufw status | grep -q "Status: active"; then
  ufw allow "$PORT"/tcp >/dev/null && echo "Pare-feu ufw : port $PORT ouvert."
elif command -v firewall-cmd >/dev/null && firewall-cmd --state >/dev/null 2>&1; then
  firewall-cmd --permanent --add-port="$PORT"/tcp >/dev/null && firewall-cmd --reload >/dev/null && echo "Pare-feu firewalld : port $PORT ouvert."
fi

# ---------------------------------------------------------------- vérification
say "Vérification"
sleep 3
URL="http://127.0.0.1:$PORT$URL_PREFIX/connexion/"
if command -v curl >/dev/null && curl -fsS -o /dev/null "$URL"; then
  echo "AHMIS répond sur $URL"
else
  warn "AHMIS ne répond pas encore. Diagnostic : systemctl status ahmis ; journalctl -u ahmis -n 50 ; tail $DATA_DIR/logs/ahmis.log"
fi

IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
[ "$PORT" = 80 ] && SUFFIX="" || SUFFIX=":$PORT"
cat <<EOF

============================================================
 AHMIS est installé.
   Adresse      : http://${SERVER_NAME:-$IP}$SUFFIX$URL_PREFIX/
EOF
if [ "$DEMO" = 1 ]; then
  echo "   Comptes      : admin, camo, planif, meca, b1, b2, certc, magasin, qualite – mot de passe Ahmis2026!"
elif [ "${GENERATED_PW:-0}" = 1 ]; then
  echo "   Compte admin : admin / $ADMIN_PW   (notez-le, il ne sera plus affiché)"
fi
cat <<EOF
   Configuration: $ENV_FILE   (puis : systemctl restart ahmis)
   Données      : $DATA_DIR   (base, pièces jointes, journaux, sauvegardes)
   Commandes    : ahmis-manage <commande>   ex. ahmis-manage ahmis_backup
                  systemctl status|restart ahmis
   AD / SSO     : voir le tutoriel 27 (menu Aide), puis systemctl restart ahmis
============================================================
EOF
