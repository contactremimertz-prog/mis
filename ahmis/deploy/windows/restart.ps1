#Requires -Version 5.1
# AHMIS - redémarre le service (à lancer en administrateur après une modification de ahmis.env)
param([string]$InstallDir = "$env:ProgramFiles\AHMIS")
Stop-ScheduledTask -TaskName "AHMIS" -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*serve.py*" -and $_.ExecutablePath -like "$InstallDir*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Start-ScheduledTask -TaskName "AHMIS"
Write-Host "AHMIS redémarré."
