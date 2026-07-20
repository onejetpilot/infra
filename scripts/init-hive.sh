#!/usr/bin/env bash
set -euo pipefail
users_csv="${HDFS_USERS:-${HDFS_USER:-student}}"
IFS=',' read -ra users <<< "$users_csv"
for raw_user in "${users[@]}"; do
  user="${raw_user//[[:space:]]/}"
  [[ "$user" =~ ^[a-zA-Z][a-zA-Z0-9._-]*$ ]] || { echo "ERROR: invalid Hive user: $raw_user" >&2; exit 2; }
  database="${user//[^a-zA-Z0-9_]/_}_db"
  beeline -u 'jdbc:hive2://hiveserver2:10000/default' -n "$user" --silent=true -e \
    "CREATE DATABASE IF NOT EXISTS \`${database}\` LOCATION 'hdfs://namenode:8020/user/${user}/hive';"
done
