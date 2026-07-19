#!/usr/bin/env bash
set -euo pipefail
if [[ "${CONFIRM_RESET:-}" != DELETE ]]; then echo 'Отказ: запустите с CONFIRM_RESET=DELETE' >&2; exit 2; fi
docker compose down -v --remove-orphans

