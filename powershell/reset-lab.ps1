param([switch]$Confirm)
$ErrorActionPreference = 'Stop'
if (-not $Confirm) { throw 'Повторите с -Confirm: volumes будут удалены.' }
docker compose down -v --remove-orphans

