#!/usr/bin/env bash
set -euo pipefail
users_csv="${HDFS_USERS:-${HDFS_USER:-student}}"; overwrite="${OVERWRITE:-false}"
IFS=',' read -ra users <<< "$users_csv"
for raw_user in "${users[@]}"; do
 user="${raw_user//[[:space:]]/}"
 [[ "$user" =~ ^[a-zA-Z][a-zA-Z0-9._-]*$ ]] || { echo "ERROR: invalid HDFS user: $raw_user" >&2; exit 2; }
 for dataset in ebay yandex google; do
  src="/opt/lab/data/$dataset"; dst="/user/$user/$dataset"
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
  hdfs dfs -chown -R "$user:supergroup" "$dst"
 done
 hdfs dfs -setrep -R -w 2 "/user/$user/ebay"
 hdfs dfs -ls -R "/user/$user"
done
