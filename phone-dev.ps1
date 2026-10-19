# Run Brights so you can open it on your phone (phone and laptop on the same Wi-Fi or hotspot).
# Usage, from the brights folder:   .\phone-dev.ps1
#
# It finds this laptop's current network address and starts both servers with that address
# allowed, so you never have to edit .env when the address changes. Nothing is saved:
# the settings only apply to the two server windows it opens.

$ErrorActionPreference = 'Stop'

# The network connection that reaches the internet (Wi-Fi or phone hotspot).
$ip = Get-NetIPConfiguration |
  Where-Object { $_.IPv4DefaultGateway -and $_.NetAdapter.Status -eq 'Up' } |
  ForEach-Object { $_.IPv4Address.IPAddress } |
  Where-Object { $_ -and $_ -notlike '169.254.*' } |
  Select-Object -First 1

if (-not $ip) {
  Write-Host "Couldn't find this laptop's network address. Connect to Wi-Fi (or your phone's hotspot) and try again." -ForegroundColor Red
  exit 1
}

$url = "http://${ip}:5173"

# These override the matching lines in backend\.env for the servers started below.
$env:DJANGO_ALLOWED_HOSTS = "localhost,127.0.0.1,$ip"
$env:DJANGO_CSRF_TRUSTED_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173,$url"
$env:FRONTEND_URL = $url   # so email links (verify, password reset) open on the phone

$root = $PSScriptRoot
Start-Process powershell -ArgumentList '-NoExit', '-Command', "Set-Location '$root\backend'; .\venv\Scripts\Activate.ps1; python manage.py runserver"
Start-Process powershell -ArgumentList '-NoExit', '-Command', "Set-Location '$root\frontend'; npm run dev -- --host"

Write-Host ""
Write-Host "Two server windows are starting. On your phone, open:" -ForegroundColor Green
Write-Host "   $url" -ForegroundColor Green
Write-Host ""
Write-Host "Not loading? Make sure the phone is on the same Wi-Fi, Windows calls the network 'Private',"
Write-Host "and you allowed Node.js through the firewall. Close the two windows to stop the servers."
