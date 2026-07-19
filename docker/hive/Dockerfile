ARG HIVE_VERSION=3.1.3
FROM apache/hive:${HIVE_VERSION}
USER root
ARG POSTGRES_JDBC_VERSION=42.7.5
RUN find /opt/hive/lib -maxdepth 1 -type f -iname 'postgresql-*.jar' -delete
ADD https://repo1.maven.org/maven2/org/postgresql/postgresql/${POSTGRES_JDBC_VERSION}/postgresql-${POSTGRES_JDBC_VERSION}.jar /opt/hive/lib/postgres.jar
RUN chmod 0644 /opt/hive/lib/postgres.jar
COPY docker/hive/hive-entrypoint.sh /opt/lab/bin/hive-entrypoint.sh
RUN chmod 0755 /opt/lab/bin/hive-entrypoint.sh
USER hive
ENTRYPOINT ["/opt/lab/bin/hive-entrypoint.sh"]
