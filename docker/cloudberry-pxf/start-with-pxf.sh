#!/usr/bin/env bash
set -euo pipefail

export GPHOME=/usr/local/cloudberry-db
export PXF_HOME=/usr/local/pxf
export PXF_BASE=/home/gpadmin/pxf-base
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
export PATH="${PXF_HOME}/bin:${GPHOME}/bin:${PATH}"

"${PXF_HOME}/bin/pxf" start

if [[ "${HOSTNAME}" == "cdw" ]]; then
    if [[ -d /home/gpadmin/gpfdist ]]; then
        if ! pgrep -x gpfdist >/dev/null; then
            nohup gpfdist \
                -d /home/gpadmin/gpfdist \
                -p 8080 \
                -l /tmp/gpfdist.log \
                >/tmp/gpfdist.stdout 2>&1 &
        fi
    fi

    if [[ -f /data0/database/coordinator/gpseg-1/PG_VERSION ]]; then
        export MASTER_DATA_DIRECTORY=/data0/database/coordinator/gpseg-1
        gpstart -a
        exec tail -f /dev/null
    fi
fi

exec /tmp/init_system.sh
