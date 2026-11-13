#Requires -Version 5.1
<#
.SYNOPSIS  AHMIS - désinstallation Windows.
.EXAMPLE   powershell -ExecutionPolicy Bypass -File uninstall.ps1          # conserve les données
.EXAMPLE   powershell -ExecutionPolicy Bypass -File uninstall.ps1 -Purge   # supprime aussi C:\ProgramData\AHMIS
#>
param([switch]$Purge, [string]$InstallDir = "$env:ProgramFiles\AHMIS", [string]$DataDir = "$env:ProgramData\AHMIS")
$ErrorActionPreference = "Continue"
foreach ($t in "AHMIS", "AHMIS - sauvegarde") {
    Stop-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $t -Confirm:$false -ErrorAction SilentlyContinue
}
Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*serve.py*" -and $_.ExecutablePath -like "$InstallDir*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Get-NetFirewallRule -DisplayName "AHMIS" -ErrorAction SilentlyContinue | Remove-NetFirewallRule
[Environment]::SetEnvironmentVariable("AHMIS_ENV_FILE", $null, "Machine")
Remove-Item -Recurse -Force $InstallDir -ErrorAction SilentlyContinue
if ($Purge) {
    Remove-Item -Recurse -Force $DataDir -ErrorAction SilentlyContinue
    Write-Host "AHMIS désinstallé, données supprimées."
} else {
    Write-Host "AHMIS désinstallé. Données et configuration conservées dans $DataDir"
}
