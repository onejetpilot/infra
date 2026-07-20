param([switch]$Overwrite)
$ErrorActionPreference = 'Stop'
$value = if ($Overwrite) { 'true' } else { 'false' }
docker compose exec -T -e OVERWRITE=$value namenode bash /opt/lab/scripts/upload-data.sh
