#!/usr/bin/env bash
set -euo pipefail
users_csv="${HDFS_USERS:-${HDFS_USER:-student}}"
until hdfs dfsadmin -safemode get 2>/dev/null | grep -q OFF; do sleep 2; done
hdfs dfs -mkdir -p /user /user/hive/warehouse /data/raw
hdfs dfs -mkdir -p /data/raw/ebay /data/raw/yndx_metrica/parquet /data/raw/google_analytics
hdfs dfs -chown -R root:supergroup /data
hdfs dfs -chmod 0555 /data /data/raw
hdfs dfs -chmod -R 0555 /data/raw
hdfs dfs -mkdir -p /tmp /tmp/hive
IFS=',' read -ra users <<< "$users_csv"
for raw_user in "${users[@]}"; do
  user="${raw_user//[[:space:]]/}"
  [[ "$user" =~ ^[a-zA-Z][a-zA-Z0-9._-]*$ ]] || { echo "ERROR: invalid HDFS user: $raw_user" >&2; exit 2; }
  base="/user/$user"
  hdfs dfs -mkdir -p "$base"
  for dir in hive ebay_listings_optimized ebay_snowflake hadoop_training spark_training; do hdfs dfs -mkdir -p "$base/$dir"; done
  hdfs dfs -chown -R "$user:supergroup" "$base"
  hdfs dfs -chmod 0750 "$base"
  hdfs dfs -chmod -R u+rwX,g+rX,o-rwx "$base"
  # HS2 checks DDL paths as its service account even when doAs is enabled.
  hdfs dfs -setfacl -m user:hive:r-x "$base"
  hdfs dfs -setfacl -m user:hive:rwx "$base/hive"
  hdfs dfs -setrep -R 2 "$base" >/dev/null
  hdfs dfs -ls "$base"
done

# Personal Greenplum/PXF area. Jupyter prepares output directories as the
# student, while PXF writes files as gpadmin.
greenplum_schema="${GREENPLUM_SCHEMA:-m_razhin}"
greenplum_user="${GREENPLUM_HDFS_USER:-gpadmin}"
[[ "$greenplum_schema" =~ ^[a-zA-Z][a-zA-Z0-9._-]*$ ]] || { echo "ERROR: invalid Greenplum schema: $greenplum_schema" >&2; exit 2; }
[[ "$greenplum_user" =~ ^[a-zA-Z][a-zA-Z0-9._-]*$ ]] || { echo "ERROR: invalid Greenplum HDFS user: $greenplum_user" >&2; exit 2; }
greenplum_base="/data/raw/$greenplum_schema"
hdfs dfs -mkdir -p "$greenplum_base"
hdfs dfs -setfacl -m "user::rwx,user:${HDFS_USER:-student}:rwx,user:$greenplum_user:rwx,mask::rwx" "$greenplum_base"
hdfs dfs -setfacl -m "default:user::rwx,default:user:${HDFS_USER:-student}:rwx,default:user:$greenplum_user:rwx,default:mask::rwx" "$greenplum_base"

hdfs dfs -chown -R hive:supergroup /user/hive
hdfs dfs -chmod 1770 /user/hive/warehouse
hdfs dfs -chown root:supergroup /tmp
hdfs dfs -chmod 1777 /tmp
hdfs dfs -chown "${HDFS_USER:-student}:supergroup" /tmp/hive
hdfs dfs -chmod 0733 /tmp/hive
