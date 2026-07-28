#!/usr/bin/env bash
set -euo pipefail

export GPHOME=/usr/local/cloudberry-db
export PXF_HOME=/usr/local/pxf
export PXF_BASE=/home/gpadmin/pxf-base
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
export PATH="${PXF_HOME}/bin:${GPHOME}/bin:${PATH}"

"${PXF_HOME}/bin/pxf" start
exec /tmp/init_system.sh

