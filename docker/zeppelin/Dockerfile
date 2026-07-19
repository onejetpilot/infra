ARG ZEPPELIN_VERSION=0.11.2
FROM apache/zeppelin:${ZEPPELIN_VERSION}
USER root
ARG SPARK_VERSION=3.5.5
ARG HADOOP_VERSION=3.3.6
ARG HIVE_VERSION=3.1.3
ADD https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz /tmp/spark.tgz
ADD https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz /tmp/hadoop.tgz
ADD https://archive.apache.org/dist/hive/hive-${HIVE_VERSION}/apache-hive-${HIVE_VERSION}-bin.tar.gz /tmp/hive.tgz
RUN tar -xzf /tmp/spark.tgz -C /opt && rm /tmp/spark.tgz \
 && ln -s "/opt/spark-${SPARK_VERSION}-bin-hadoop3" /opt/spark \
 && tar -xzf /tmp/hadoop.tgz -C /opt && rm /tmp/hadoop.tgz \
 && ln -s "/opt/hadoop-${HADOOP_VERSION}" /opt/hadoop
RUN tar -xzf /tmp/hive.tgz -C /opt && rm /tmp/hive.tgz \
 && ln -s "/opt/apache-hive-${HIVE_VERSION}-bin" /opt/hive
ENV SPARK_HOME=/opt/spark HIVE_HOME=/opt/hive HADOOP_HOME=/opt/hadoop HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop PATH=/opt/spark/bin:/opt/hive/bin:/opt/hadoop/bin:$PATH
USER root
