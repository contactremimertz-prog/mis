#!/usr/bin/env bash
# AHMIS – remet la base de démonstration à zéro
set -e
cd "$(dirname "$0")"
# Démo locale : n'utilise jamais la configuration d'un serveur installé sur ce poste
export AHMIS_ENV_FILE="$PWD/ahmis.env"
. .venv/bin/activate
python manage.py migrate --noinput
python manage.py load_demo --reset
echo "Base de démonstration rechargée."
