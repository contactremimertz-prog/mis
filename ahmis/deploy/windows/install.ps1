#Requires -Version 5.1
<#
.SYNOPSIS
    AHMIS - installation serveur Windows (Windows Server 2016+ / Windows 10+).

.DESCRIPTION
    - Copie l'application dans C:\Program Files\AHMIS, les données dans C:\ProgramData\AHMIS
    - Crée l'environnement Python, installe les dépendances (en ligne ou depuis le dossier wheels\)
    - Génère la configuration (ahmis.env) avec une clé secrète aléatoire
    - Crée la base, le compte admin (ou charge la démo)
    - Démarre AHMIS en tâche planifiée au démarrage du serveur (compte LOCAL SERVICE, redémarrage auto)
    - Planifie une sauvegarde quotidienne et ouvre le port dans le pare-feu Windows
    Relancer le script avec une version plus récente = mise à jour (configuration et données conservées).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File deploy\windows\install.ps1
    powershell -ExecutionPolicy Bypass -File deploy\windows\install.ps1 -Demo -Port 80
#>
[CmdletBinding()]
param(
    [switch]$Demo,
    [string]$AdminPassword = "",
    [int]$Port = 8000,
    [string]$ServerName = "",
    [string]$InstallDir = "$env:ProgramFiles\AHMIS",
    [string]$DataDir = "$env:ProgramData\AHMIS",
    [switch]$NoFirewall
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

function Say($msg)  { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "[!] $msg" -ForegroundColor Yellow }
function Die($msg)  { Write-Host "[ERREUR] $msg" -ForegroundColor Red; exit 1 }
function New-Secret([int]$bytes = 48) {
    $b = New-Object byte[] $bytes
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b)
    return ([Convert]::ToBase64String($b)).Replace("+", "-").Replace("/", "_").TrimEnd("=")
}

# ---------------------------------------------------------------- prérequis
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Die "Lancez PowerShell en tant qu'administrateur (clic droit > Exécuter en tant qu'administrateur)."
}
$SrcDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
if (-not (Test-Path (Join-Path $SrcDir "manage.py"))) { Die "manage.py introuvable dans $SrcDir." }

Say "Recherche de Python 3.10 ou plus récent"
function Find-Python {
    $candidates = @()
    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($v in "3.14", "3.13", "3.12", "3.11", "3.10") {
            try {
                $exe = & py "-$v" -c "import sys; print(sys.executable)" 2>$null
                if ($LASTEXITCODE -eq 0 -and $exe) { $candidates += $exe.Trim() }
            } catch { }
        }
    }
    foreach ($c in "python", "python3") {
        $cmd = Get-Command $c -ErrorAction SilentlyContinue
        if ($cmd -and $cmd.Source -notlike "*WindowsApps*") { $candidates += $cmd.Source }
    }
    foreach ($exe in $candidates) {
        & $exe -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { return $exe }
    }
    return $null
}
$Py = Find-Python
if (-not $Py -and (Get-Command winget -ErrorAction SilentlyContinue)) {
    Warn "Python introuvable : installation de Python 3.13 avec winget…"
    winget install --id Python.Python.3.13 --scope machine --silent --accept-package-agreements --accept-source-agreements | Out-Host
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
    $Py = Find-Python
}
if (-not $Py) {
    Die "Python 3.10+ introuvable. Installez-le depuis https://www.python.org/downloads/windows/ (option « Install for all users » et « Add to PATH »), puis relancez."
}
Write-Host "Python : $(& $Py --version) ($Py)"
# Le compte LOCAL SERVICE doit pouvoir lire Python : refuser un Python installé dans un profil utilisateur
if ($Py -like "$env:SystemDrive\Users\*") {
    Die "Python est installé dans un profil utilisateur ($Py). Réinstallez-le « pour tous les utilisateurs » (C:\Program Files\Python3xx)."
}

# ---------------------------------------------------------------- arrêt d'une version précédente
$TaskName = "AHMIS"
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Say "Arrêt de la version en service"
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 3
    # Sécurité : arrêter un serveur AHMIS resté actif
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like "*serve.py*" -and $_.ExecutablePath -like "$InstallDir*" } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

# ---------------------------------------------------------------- copie de l'application
Say "Copie de l'application dans $InstallDir"
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Get-ChildItem -Force $InstallDir | Where-Object { $_.Name -ne ".venv" } | Remove-Item -Recurse -Force
$exclude = @(".venv", "db", "media", "staticfiles", "ahmis.env", "wheels", "__pycache__")
Get-ChildItem -Force $SrcDir | Where-Object { $exclude -notcontains $_.Name } |
    ForEach-Object { Copy-Item $_.FullName -Destination $InstallDir -Recurse -Force }
Get-ChildItem -Path $InstallDir -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

foreach ($d in "", "db", "media", "logs", "backups") {
    New-Item -ItemType Directory -Force -Path (Join-Path $DataDir $d) | Out-Null
}

# ---------------------------------------------------------------- environnement Python
Say "Environnement Python et dépendances"
$Venv = Join-Path $InstallDir ".venv"
$VPy = Join-Path $Venv "Scripts\python.exe"
if (Test-Path $VPy) {
    & $VPy -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" 2>$null
    if ($LASTEXITCODE -ne 0) { Remove-Item -Recurse -Force $Venv }
}
if (-not (Test-Path $VPy)) {
    # --copies : le compte de service n'a pas besoin d'accéder au profil de l'installateur
    & $Py -m venv --copies $Venv
    if ($LASTEXITCODE -ne 0) { Die "Création de l'environnement Python impossible." }
}
$pipArgs = @("-m", "pip", "install", "--disable-pip-version-check", "-q")
$Wheels = Join-Path $SrcDir "wheels"
if (Test-Path $Wheels) {
    Write-Host "Installation hors ligne depuis $Wheels"
    $pipArgs += @("--no-index", "--find-links", $Wheels)
} else {
    & $VPy -m pip install --disable-pip-version-check -q --upgrade pip
}
& $VPy @pipArgs -r (Join-Path $InstallDir "requirements-server.txt")
if ($LASTEXITCODE -ne 0) { Die "Installation des dépendances impossible (accès à pypi.org requis, ou dossier wheels\)." }

# ---------------------------------------------------------------- configuration
Say "Configuration"
$EnvFile = Join-Path $DataDir "ahmis.env"
if (-not (Test-Path $EnvFile)) {
    $hosts = @("localhost", "127.0.0.1", $env:COMPUTERNAME.ToLower())
    try {
        $fqdn = [System.Net.Dns]::GetHostEntry("").HostName.ToLower()
        if ($fqdn -and $hosts -notcontains $fqdn) { $hosts += $fqdn }
    } catch { }
    Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } |
        ForEach-Object { $hosts += $_.IPAddress }
    if ($ServerName) { $hosts += $ServerName }
    $suffix = if ($Port -eq 80) { "" } else { ":$Port" }
    $origins = ($hosts | ForEach-Object { "http://$_$suffix" }) -join ","
    $content = Get-Content -Raw -Encoding UTF8 (Join-Path $InstallDir "deploy\ahmis.env.exemple")
    $content = $content -replace "(?m)^AHMIS_SECRET_KEY=.*$", "AHMIS_SECRET_KEY=$(New-Secret 64)"
    $content = $content -replace "(?m)^AHMIS_ALLOWED_HOSTS=.*$", "AHMIS_ALLOWED_HOSTS=$($hosts -join ',')"
    $content = $content -replace "(?m)^AHMIS_CSRF_TRUSTED_ORIGINS=.*$", "AHMIS_CSRF_TRUSTED_ORIGINS=$origins"
    $content = $content -replace "(?m)^AHMIS_DATA_DIR=.*$", "AHMIS_DATA_DIR=$DataDir"
    $content = $content -replace "(?m)^AHMIS_BIND=.*$", "AHMIS_BIND=0.0.0.0:$Port"
    $content = $content -replace "(?m)^AHMIS_DEMO=.*$", "AHMIS_DEMO=$(if ($Demo) { 1 } else { 0 })"
    $content += "`r`nAHMIS_STATIC_ROOT=$InstallDir\staticfiles`r`n"
    [IO.File]::WriteAllText($EnvFile, $content, (New-Object Text.UTF8Encoding($false)))
    Write-Host "Fichier de configuration créé : $EnvFile"
} else {
    Write-Host "Configuration existante conservée : $EnvFile"
}
$env:AHMIS_ENV_FILE = $EnvFile

# Droits : données lisibles uniquement par les administrateurs, SYSTEM et le compte de service
Say "Droits d'accès sur $DataDir"
& icacls $DataDir /inheritance:r /grant:r "*S-1-5-32-544:(OI)(CI)F" "*S-1-5-18:(OI)(CI)F" "*S-1-5-19:(OI)(CI)M" | Out-Null
& icacls $EnvFile /inheritance:r /grant:r "*S-1-5-32-544:F" "*S-1-5-18:F" "*S-1-5-19:R" | Out-Null

# Commande d'administration : ahmis-manage <commande>
$ManageCmd = Join-Path $InstallDir "ahmis-manage.cmd"
@"
@echo off
set AHMIS_ENV_FILE=$EnvFile
"$VPy" "$InstallDir\manage.py" %*
"@ | Set-Content -Encoding ASCII $ManageCmd

# ---------------------------------------------------------------- base de données
Say "Base de données et fichiers statiques"
Push-Location $InstallDir
try {
    & $VPy manage.py collectstatic --noinput -v0;  if ($LASTEXITCODE -ne 0) { Die "collectstatic a échoué." }
    & $VPy manage.py migrate --noinput;            if ($LASTEXITCODE -ne 0) { Die "migrate a échoué." }
    $GeneratedPw = $false
    if ($Demo) {
        & $VPy manage.py load_demo
    } else {
        & $VPy manage.py shell -c "from django.contrib.auth import get_user_model as g; import sys; sys.exit(0 if g().objects.filter(username='admin').exists() else 1)" 2>$null
        $adminExists = ($LASTEXITCODE -eq 0)
        if (-not $adminExists -and -not $AdminPassword) { $AdminPassword = New-Secret 12; $GeneratedPw = $true }
        $env:AHMIS_ADMIN_PASSWORD = $AdminPassword
        & $VPy manage.py ahmis_init
        Remove-Item Env:\AHMIS_ADMIN_PASSWORD -ErrorAction SilentlyContinue
        if ($LASTEXITCODE -ne 0) { Die "Initialisation impossible (mot de passe trop faible ?)." }
    }
} finally { Pop-Location }
# Base créée par l'administrateur : donner l'écriture au compte de service
& icacls (Join-Path $DataDir "db") /grant "*S-1-5-19:(OI)(CI)M" /T | Out-Null
& icacls (Join-Path $DataDir "logs") /grant "*S-1-5-19:(OI)(CI)M" /T | Out-Null

# ---------------------------------------------------------------- tâches planifiées (service)
Say "Démarrage automatique (tâche planifiée « $TaskName »)"
# Le compte de service doit pouvoir lire l'application et l'installation Python de base
$BasePy = (& $VPy -c "import sys; print(sys.base_prefix)").Trim()
& icacls $InstallDir /grant "*S-1-5-19:(OI)(CI)RX" /T /Q | Out-Null
& icacls $BasePy /grant "*S-1-5-19:(OI)(CI)RX" /T /Q | Out-Null
$svcPrincipal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\LOCALSERVICE" -LogonType ServiceAccount -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
    -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
$action = New-ScheduledTaskAction -Execute $VPy -Argument "`"$InstallDir\serve.py`"" -WorkingDirectory $InstallDir
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName $TaskName -Description "AHMIS - Maintenance Information System" -Action $action `
    -Trigger $trigger -Principal $svcPrincipal -Settings $settings -Force | Out-Null

$bkAction = New-ScheduledTaskAction -Execute $VPy -Argument "`"$InstallDir\manage.py`" ahmis_backup --keep 30" -WorkingDirectory $InstallDir
$bkTrigger = New-ScheduledTaskTrigger -Daily -At "02:30"
$bkPrincipal = New-ScheduledTaskPrincipal -UserId "NT AUTHORITY\SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$bkSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2)
Register-ScheduledTask -TaskName "AHMIS - sauvegarde" -Description "Sauvegarde quotidienne AHMIS" -Action $bkAction `
    -Trigger $bkTrigger -Principal $bkPrincipal -Settings $bkSettings -Force | Out-Null
# AHMIS trouve sa configuration dans %ProgramData%\AHMIS\ahmis.env sans variable d'environnement.
if ($DataDir -ne "$env:ProgramData\AHMIS") {
    [Environment]::SetEnvironmentVariable("AHMIS_ENV_FILE", $EnvFile, "Machine")
    Warn "Dossier de données personnalisé : variable système AHMIS_ENV_FILE définie (un redémarrage du serveur peut être nécessaire)."
}

Start-ScheduledTask -TaskName $TaskName

# ---------------------------------------------------------------- pare-feu
if (-not $NoFirewall) {
    Say "Pare-feu : ouverture du port $Port"
    Get-NetFirewallRule -DisplayName "AHMIS" -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    New-NetFirewallRule -DisplayName "AHMIS" -Direction Inbound -Protocol TCP -LocalPort $Port -Action Allow -Profile Domain, Private | Out-Null
}

# ---------------------------------------------------------------- vérification
Say "Vérification"
$ok = $false
for ($i = 0; $i -lt 20 -and -not $ok; $i++) {
    Start-Sleep -Seconds 2
    try {
        $r = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/connexion/" -TimeoutSec 5
        $ok = ($r.StatusCode -eq 200)
    } catch { }
}
if ($ok) { Write-Host "AHMIS répond sur http://127.0.0.1:$Port" -ForegroundColor Green }
else { Warn "AHMIS ne répond pas encore. Consultez $DataDir\logs\serveur.log et $DataDir\logs\ahmis.log" }

$addr = if ($ServerName) { $ServerName } else { $env:COMPUTERNAME.ToLower() }
$suffix = if ($Port -eq 80) { "" } else { ":$Port" }
Write-Host ""
Write-Host "============================================================"
Write-Host " AHMIS est installé."
Write-Host "   Adresse      : http://$addr$suffix"
if ($Demo) { Write-Host "   Comptes      : admin, camo, planif, meca, b1, b2, certc, magasin, qualite – mot de passe Ahmis2026!" }
elseif ($GeneratedPw) { Write-Host "   Compte admin : admin / $AdminPassword   (notez-le, il ne sera plus affiché)" -ForegroundColor Yellow }
Write-Host "   Configuration: $EnvFile   (puis : deploy\windows\restart.ps1)"
Write-Host "   Données      : $DataDir   (base, pièces jointes, journaux, sauvegardes)"
Write-Host "   Commandes    : `"$ManageCmd`" <commande>   ex. ahmis_backup"
Write-Host "   AD / SSO     : voir le tutoriel 27 (menu Aide)"
Write-Host "============================================================"
