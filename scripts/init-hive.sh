#!/usr/bin/env bash
set -euo pipefail
beeline -u 'jdbc:hive2://hiveserver2:10000/default' -n m.razhin --silent=true -f /opt/lab/sql/01_create_database.sql

