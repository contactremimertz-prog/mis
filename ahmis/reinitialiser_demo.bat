@echo off
REM AHMIS - remet la base de demonstration a zero
cd /d "%~dp0"
set "AHMIS_ENV_FILE=%~dp0ahmis.env"
call .venv\Scripts\activate.bat
python manage.py migrate --noinput
python manage.py load_demo --reset
echo Base de demonstration rechargee.
pause
