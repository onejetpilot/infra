$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot

try {
    docker compose up -d sql-train-db

    $ready = $false
    foreach ($attempt in 1..30) {
        docker compose exec -T sql-train-db pg_isready -U student -d sql_train 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            $ready = $true
            break
        }
        Start-Sleep -Seconds 2
    }

    if (-not $ready) {
        throw 'SQL Train PostgreSQL did not become ready in 60 seconds.'
    }

    $sqlFiles = @(
        '/workspace/sql/init/001_schemas.sql',
        '/workspace/sql/init/002_raw_tables.sql',
        '/workspace/sql/load/001_load_csv.sql',
        '/workspace/sql/transform/001_staging.sql',
        '/workspace/sql/transform/002_marts.sql',
        '/workspace/sql/quality/001_checks.sql',
        '/workspace/sql/quality/002_source_counts.sql',
        '/workspace/training/001_check_framework.sql',
        '/workspace/training/010_function_tests.sql'
    )

    foreach ($sqlFile in $sqlFiles) {
        Write-Host "Running $sqlFile"
        docker compose exec -T sql-train-db `
            psql -v ON_ERROR_STOP=1 -U student -d sql_train -f $sqlFile

        if ($LASTEXITCODE -ne 0) {
            throw "Failed to execute $sqlFile"
        }
    }

    Write-Host 'SQL Train is ready: localhost:15433 / sql_train / student / sqltrain2026'
}
finally {
    Pop-Location
}
