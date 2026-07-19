#!/usr/bin/env bash
set -euo pipefail
role="${1:?namenode or datanode required}"
if [[ "$role" == namenode ]]; then
  if [[ ! -f /data/dfs/name/current/VERSION ]]; then
    hdfs namenode -format -force -nonInteractive -clusterId hadoop-local-lab
  fi
  hdfs namenode &
  pid=$!
  trap 'kill "$pid" 2>/dev/null || true' TERM INT
  for _ in {1..60}; do hdfs dfs -test -d / 2>/dev/null && break; sleep 1; done
  hdfs dfs -test -d /
  bash /opt/lab/scripts/init-hdfs.sh
  wait "$pid"
  exit $?
fi
if [[ "$role" == datanode ]]; then exec hdfs datanode; fi
echo "Unknown role: $role" >&2; exit 2
