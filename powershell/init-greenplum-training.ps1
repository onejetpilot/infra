$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    $sqlFiles = @(
        '001_check_framework.sql',
        '010_distribution_tests.sql',
        '020_storage_partitioning_tests.sql',
        '030_query_optimization_tests.sql',
        '040_gpfdist_tests.sql',
        '050_pxf_hdfs_tests.sql',
        '060_etl_tests.sql',
        '070_data_marts_tests.sql',
        '080_administration_tests.sql'
    )
    foreach ($sqlFile in $sqlFiles) {
        docker cp `
            "$projectRoot/training/greenplum/sql/$sqlFile" `
            "cbdb-cdw3:/tmp/$sqlFile"
        docker compose exec -T cbdb-coordinator `
            psql -v ON_ERROR_STOP=1 -d moex -f "/tmp/$sqlFile"
        if ($LASTEXITCODE -ne 0) {
            throw "Greenplum training initialization failed on $sqlFile."
        }
    }
    Write-Host 'Greenplum training is ready in database moex, schema greenplum_training.'
}
finally {
    Pop-Location
}
