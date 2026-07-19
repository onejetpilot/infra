#!/usr/bin/env bash
set -euo pipefail

# The upstream Hive 3.1.3 image unconditionally prepends Tez 0.9.1 to the
# HiveServer2 classpath. That Tez distribution contains Hadoop 2.7 client
# jars, which conflict with the image's Hadoop 3 runtime when Hive uses the
# MapReduce execution engine (NoClassDefFoundError: hadoop.metrics.Updater).
# Start HS2 directly for the MR-only local lab and keep Tez out of its
# classpath. YARN/Tez are intentionally not part of this stack.
if [[ "${SERVICE_NAME:-}" == hiveserver2 ]]; then
  export HIVE_CONF_DIR="${HIVE_CUSTOM_CONF_DIR:-/opt/hive/conf}"
  export HADOOP_CONF_DIR="$HIVE_CONF_DIR"
  export HADOOP_CLIENT_OPTS="${HADOOP_CLIENT_OPTS:-} -Xmx1G ${SERVICE_OPTS:-}"
  unset HADOOP_CLASSPATH TEZ_CONF_DIR
  exec /opt/hive/bin/hive --skiphadoopversion --skiphbasecp --service hiveserver2
fi

if [[ "${SERVICE_NAME:-}" == metastore ]]; then
  export HIVE_CONF_DIR="${HIVE_CUSTOM_CONF_DIR:-/opt/hive/conf}"
  export HADOOP_CONF_DIR="$HIVE_CONF_DIR"
  export HADOOP_CLIENT_OPTS="${HADOOP_CLIENT_OPTS:-} ${SERVICE_OPTS:-}"
  if /opt/hive/bin/schematool -dbType "${DB_DRIVER:-derby}" -info >/dev/null 2>&1; then
    export IS_RESUME=true
  fi
fi
exec /entrypoint.sh
