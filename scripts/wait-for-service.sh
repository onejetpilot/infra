#!/usr/bin/env bash
set -euo pipefail
host="${1:?host}" port="${2:?port}" timeout="${3:-120}"
for ((i=0; i<timeout; i++)); do (echo >/dev/tcp/"$host"/"$port") >/dev/null 2>&1 && exit 0; sleep 1; done
echo "Timeout waiting for $host:$port" >&2; exit 1

