ARG HADOOP_VERSION=3.3.6
FROM eclipse-temurin:11-jre-jammy
ARG HADOOP_VERSION
ADD https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz /tmp/hadoop.tar.gz
RUN apt-get update && apt-get install -y --no-install-recommends curl tini procps && rm -rf /var/lib/apt/lists/* \
 && tar -xzf /tmp/hadoop.tar.gz -C /opt && rm /tmp/hadoop.tar.gz \
 && ln -s "/opt/hadoop-${HADOOP_VERSION}" /opt/hadoop
ENV HADOOP_HOME=/opt/hadoop HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop PATH=/opt/hadoop/bin:/opt/hadoop/sbin:$PATH
COPY docker/hadoop/hadoop-entrypoint.sh /opt/lab/bin/hadoop-entrypoint.sh
RUN chmod 0755 /opt/lab/bin/hadoop-entrypoint.sh
ENTRYPOINT ["/usr/bin/tini", "--"]
