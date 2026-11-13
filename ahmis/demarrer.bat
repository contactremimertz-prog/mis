@echo off
setlocal EnableDelayedExpansion
REM AHMIS - demarrage de la demo (Windows)
cd /d "%~dp0"
REM Demo locale : n'utilise jamais la configuration d'un serveur installe sur ce poste
set "AHMIS_ENV_FILE=%~dp0ahmis.env"

REM Recherche d'un Python 3.10 ou plus recent
set "PY="
for %%V in (3.14 3.13 3.12 3.11 3.10) do (
  if not defined PY (
    py -%%V -c "import sys" >nul 2>nul && set "PY=py -%%V"
  )
)
if not defined PY (
  python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo Python 3.10 ou plus recent est requis : https://www.python.org/downloads/windows/
  echo Cochez "Add python.exe to PATH" pendant l'installation, puis relancez ce script.
  pause
  exit /b 1
)
echo Python utilise : 
%PY% --version

if exist .venv\Scripts\python.exe (
  .venv\Scripts\python.exe -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul || rmdir /s /q .venv
)
if not exist .venv\Scripts\python.exe (
  echo Creation de l'environnement Python - premiere execution
  %PY% -m venv .venv || (pause & exit /b 1)
)
call .venv\Scripts\activate.bat
pip install -q --disable-pip-version-check -r requirements.txt || (pause & exit /b 1)
python manage.py migrate --noinput || (pause & exit /b 1)
python manage.py load_demo
echo.
echo AHMIS est disponible sur http://127.0.0.1:8000  (fermer cette fenetre pour arreter)
start "" http://127.0.0.1:8000
python manage.py runserver 127.0.0.1:8000
pause
