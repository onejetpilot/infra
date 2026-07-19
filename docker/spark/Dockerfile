ARG SPARK_VERSION=3.5.5
FROM eclipse-temurin:11-jre-jammy
ARG SPARK_VERSION
ARG HADOOP_VERSION=3.3.6
ARG HIVE_VERSION=3.1.3
ADD https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz /tmp/spark.tgz
ADD https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz /tmp/hadoop.tgz
ADD https://archive.apache.org/dist/hive/hive-${HIVE_VERSION}/apache-hive-${HIVE_VERSION}-bin.tar.gz /tmp/hive.tgz
RUN apt-get update && apt-get install -y --no-install-recommends curl tini procps python3 python3-pip && rm -rf /var/lib/apt/lists/* \
 && tar -xzf /tmp/spark.tgz -C /opt && rm /tmp/spark.tgz \
 && ln -s "/opt/spark-${SPARK_VERSION}-bin-hadoop3" /opt/spark \
 && tar -xzf /tmp/hadoop.tgz -C /opt && rm /tmp/hadoop.tgz \
 && ln -s "/opt/hadoop-${HADOOP_VERSION}" /opt/hadoop
RUN tar -xzf /tmp/hive.tgz -C /opt && rm /tmp/hive.tgz \
 && ln -s "/opt/apache-hive-${HIVE_VERSION}-bin" /opt/hive
ENV SPARK_HOME=/opt/spark HADOOP_HOME=/opt/hadoop HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop PYSPARK_PYTHON=python3 PATH=/opt/spark/bin:/opt/spark/sbin:/opt/hadoop/bin:$PATH
COPY config/spark/spark-defaults.conf /opt/spark/conf/spark-defaults.conf
COPY config/spark/log4j2.properties /opt/spark/conf/log4j2.properties
ENTRYPOINT ["/usr/bin/tini", "--"]
