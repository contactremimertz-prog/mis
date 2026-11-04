#!/usr/bin/env bash
# AHMIS – démarrage de la démo (macOS / Linux)
set -e
cd "$(dirname "$0")"
# Démo locale : n'utilise jamais la configuration d'un serveur installé sur ce poste
export AHMIS_ENV_FILE="$PWD/ahmis.env"

# Cherche un Python 3.10+ (le python3 d'Apple est souvent en 3.9, trop ancien pour Django 5.2)
PY=""
for c in ${PYTHON:-} python3.13 python3.12 python3.11 python3.10 \
         /Library/Frameworks/Python.framework/Versions/Current/bin/python3 \
         /opt/homebrew/bin/python3 /usr/local/bin/python3 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo ""
  echo "Python 3.10 ou plus récent est requis (version trouvée : $(python3 --version 2>&1))."
  echo "Installez la dernière version depuis https://www.python.org/downloads/macos/"
  echo "puis relancez : bash demarrer.sh"
  exit 1
fi
echo "Python utilisé : $("$PY" --version) ($PY)"

# Recrée l'environnement s'il a été créé avec un Python trop ancien
if [ -d .venv ] && ! .venv/bin/python -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
  echo "Ancien environnement Python détecté : suppression et recréation…"
  rm -rf .venv
fi
if [ ! -d .venv ]; then
  echo "Création de l'environnement Python (première exécution)…"
  "$PY" -m venv .venv
fi
. .venv/bin/activate
pip install -q --disable-pip-version-check -r requirements.txt
python manage.py migrate --noinput
python manage.py load_demo   # ne fait rien si la base contient déjà des données
echo ""
echo "AHMIS est disponible sur http://127.0.0.1:8000  (Ctrl+C pour arrêter)"
( sleep 2; (command -v open >/dev/null && open http://127.0.0.1:8000) || (command -v xdg-open >/dev/null && xdg-open http://127.0.0.1:8000) ) >/dev/null 2>&1 &
python manage.py runserver 127.0.0.1:8000
