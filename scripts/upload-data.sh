#!/usr/bin/env bash
set -euo pipefail
overwrite="${OVERWRITE:-false}"
hdfs dfs -mkdir -p /data/raw
declare -A targets=(
  [ebay]="/data/raw/ebay"
  [yandex]="/data/raw/yndx_metrica/parquet"
  [google]="/data/raw/google_analytics"
)
for dataset in ebay yandex google; do
  src="/opt/lab/data/$dataset"; dst="${targets[$dataset]}"
  hdfs dfs -mkdir -p "$dst"
  mapfile -d '' files < <(find "$src" -type f ! -name .gitkeep -print0)
  if (( ${#files[@]} == 0 )); then echo "INFO: data/$dataset пуст, пропуск"; continue; fi
  existing="$(hdfs dfs -ls -R "$dst" 2>/dev/null | awk '$1 ~ /^-/ { print; exit }' || true)"
  if [[ -n "$existing" && "$overwrite" != true ]]; then
    echo "INFO: $dst уже содержит данные, пропуск (для замены задайте OVERWRITE=true)"
    continue
  fi
  [[ "$overwrite" == true ]] && hdfs dfs -rm -r -skipTrash "$dst"/* 2>/dev/null || true
  # Copy top-level entries instead of a flattened list of files. This keeps
  # Hive-style partition directories such as snapshot_dt=2026-07-17 intact.
  shopt -s nullglob
  entries=("$src"/*)
  hdfs dfs -put "${entries[@]}" "$dst/"
  hdfs dfs -chown -R root:supergroup "$dst"
  hdfs dfs -chmod -R 0555 "$dst"
  hdfs dfs -setrep -R -w 2 "$dst"
done
hdfs dfs -chown -R root:supergroup /data
hdfs dfs -chmod 0555 /data /data/raw
hdfs dfs -ls -R /data/raw
