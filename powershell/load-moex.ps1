param(
    [string]$Ticker = 'RASP',
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^\d{4}-\d{2}-\d{2}$')]
    [string]$TradeDate,
    [string]$StudentSchema = 'm_razhin'
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$relativeFile = "data/moex/secid=$Ticker/trade_session_date=$TradeDate/trades.parquet"
$localFile = Join-Path $repoRoot $relativeFile
$hdfsDir = "/moex_labs/raw/trades/secid=$Ticker/trade_session_date=$TradeDate"

Push-Location $repoRoot
try {
    python scripts/load_moex.py --ticker $Ticker --date $TradeDate
    if ($LASTEXITCODE -ne 0) { throw 'MOEX download failed' }

    docker cp $localFile 'hadoop-local-lab-namenode-1:/tmp/moex-trades.parquet'
    if ($LASTEXITCODE -ne 0) { throw 'docker cp failed' }

    docker compose exec -T namenode hdfs dfs -mkdir -p $hdfsDir
    docker compose exec -T namenode hdfs dfs -put -f /tmp/moex-trades.parquet "$hdfsDir/trades.parquet"
    docker compose exec -T namenode hdfs dfs -chmod -R 755 /moex_labs
    if ($LASTEXITCODE -ne 0) { throw 'HDFS upload failed' }

    Get-Content sql/moex_external.sql -Raw |
        docker compose exec -T cbdb-coordinator psql -d moex `
            -v "student_schema=$StudentSchema" `
            -v "ticker=$Ticker" `
            -v "trade_date=$TradeDate"
    if ($LASTEXITCODE -ne 0) { throw 'PXF external table creation failed' }
}
finally {
    Pop-Location
}
