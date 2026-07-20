$ErrorActionPreference = 'Stop'
docker compose exec -T namenode bash /opt/lab/scripts/init-hdfs.sh
docker compose exec -T hiveserver2 bash /opt/lab/scripts/init-hive.sh
