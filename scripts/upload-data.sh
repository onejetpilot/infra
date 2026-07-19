#!/usr/bin/env bash
set -euo pipefail
user="${HDFS_USER:-m.razhin}"; overwrite="${OVERWRITE:-false}"
for dataset in ebay yandex google; do
  src="/opt/lab/data/$dataset"; dst="/user/$user/$dataset"
  mapfile -d '' files < <(find "$src" -type f ! -name .gitkeep -print0)
  if (( ${#files[@]} == 0 )); then echo "INFO: data/$dataset пуст, пропуск"; continue; fi
  existing="$(hdfs dfs -ls -R "$dst" 2>/dev/null | awk '$1 ~ /^-/ { print; exit }' || true)"
  if [[ -n "$existing" && "$overwrite" != true ]]; then echo "ERROR: $dst уже содержит данные; задайте OVERWRITE=true" >&2; exit 2; fi
  [[ "$overwrite" == true ]] && hdfs dfs -rm -r -skipTrash "$dst"/* 2>/dev/null || true
  # Copy top-level entries instead of a flattened list of files. This keeps
  # Hive-style partition directories such as snapshot_dt=2026-07-17 intact.
  shopt -s nullglob
  entries=("$src"/*)
  hdfs dfs -put "${entries[@]}" "$dst/"
  hdfs dfs -chown -R "$user:supergroup" "$dst"
done
hdfs dfs -setrep -R -w 2 "/user/$user/ebay"
hdfs dfs -ls -R "/user/$user"
