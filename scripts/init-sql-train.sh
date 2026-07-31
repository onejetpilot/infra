#!/usr/bin/env bash
set -euo pipefail

docker compose up -d sql-train-db

for _ in $(seq 1 30); do
    if docker compose exec -T sql-train-db \
        pg_isready -U student -d sql_train >/dev/null 2>&1; then
        break
    fi
    sleep 2
done

docker compose exec -T sql-train-db \
    pg_isready -U student -d sql_train >/dev/null

sql_files=(
    /workspace/sql/init/001_schemas.sql
    /workspace/sql/init/002_raw_tables.sql
    /workspace/sql/load/001_load_csv.sql
    /workspace/sql/transform/001_staging.sql
    /workspace/sql/transform/002_marts.sql
    /workspace/sql/quality/001_checks.sql
    /workspace/sql/quality/002_source_counts.sql
    /workspace/training/001_check_framework.sql
    /workspace/training/010_function_tests.sql
)

for sql_file in "${sql_files[@]}"; do
    echo "Running ${sql_file}"
    docker compose exec -T sql-train-db \
        psql -v ON_ERROR_STOP=1 -U student -d sql_train -f "${sql_file}"
done

echo "SQL Train is ready: localhost:15433 / sql_train / student / sqltrain2026"
