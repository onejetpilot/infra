#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
sql_files=(
  001_check_framework.sql
  010_distribution_tests.sql
  020_storage_partitioning_tests.sql
  030_query_optimization_tests.sql
  040_gpfdist_tests.sql
  050_pxf_hdfs_tests.sql
  060_etl_tests.sql
  070_data_marts_tests.sql
  080_administration_tests.sql
)

for sql_file in "${sql_files[@]}"; do
  docker cp \
    "${project_root}/training/greenplum/sql/${sql_file}" \
    "cbdb-cdw3:/tmp/${sql_file}"
  docker compose -f "${project_root}/compose.yaml" exec -T cbdb-coordinator \
    psql -v ON_ERROR_STOP=1 -d moex -f "/tmp/${sql_file}"
done

echo "Greenplum training is ready: moex / greenplum_training / 240 tasks."
