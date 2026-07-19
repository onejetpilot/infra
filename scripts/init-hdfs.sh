#!/usr/bin/env bash
set -euo pipefail
user="${HDFS_USER:-m.razhin}"
base="/user/$user"
until hdfs dfsadmin -safemode get 2>/dev/null | grep -q OFF; do sleep 2; done
hdfs dfs -mkdir -p /user /user/hive/warehouse "$base"
hdfs dfs -mkdir -p /tmp /tmp/hive
for dir in ebay yandex google hive ebay_listings_optimized ebay_snowflake; do hdfs dfs -mkdir -p "$base/$dir"; done
hdfs dfs -chown -R "$user:supergroup" "$base"
hdfs dfs -chmod 0750 "$base"
hdfs dfs -chmod -R u+rwX,g+rX,o-rwx "$base"
# HS2 performs some DDL filesystem checks as its service account even with doAs enabled.
hdfs dfs -setfacl -m user:hive:r-x "$base"
hdfs dfs -setfacl -m user:hive:rwx "$base/hive"
hdfs dfs -chown -R hive:supergroup /user/hive
hdfs dfs -chmod 1770 /user/hive/warehouse
hdfs dfs -chown root:supergroup /tmp
hdfs dfs -chmod 1777 /tmp
hdfs dfs -chown "$user:supergroup" /tmp/hive
hdfs dfs -chmod 0733 /tmp/hive
hdfs dfs -setrep -R 2 "$base" >/dev/null
hdfs dfs -ls "$base"
