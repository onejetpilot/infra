FROM mcold/cbdb:1.6.0-rockylinux9

USER root

RUN dnf install -y java-11-openjdk-devel libcurl-devel rsync \
    && dnf clean all \
    && rm -rf /var/cache/dnf

COPY vendor/cloudberry-pxf /tmp/cloudberry-pxf-checkout

RUN cd /tmp/cloudberry-pxf-checkout \
    && git config core.autocrlf false \
    && mkdir -p /tmp/cloudberry-pxf \
    && git checkout-index -a -f --prefix=/tmp/cloudberry-pxf/ \
    && mkdir -p /usr/local/pxf /home/gpadmin/pxf-base \
    && chown -R gpadmin:gpadmin \
        /tmp/cloudberry-pxf \
        /usr/local/pxf \
        /home/gpadmin/pxf-base \
        /usr/local/cloudberry-db

USER gpadmin

ENV GPHOME=/usr/local/cloudberry-db
ENV PXF_HOME=/usr/local/pxf
ENV PXF_BASE=/home/gpadmin/pxf-base
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk
ENV PATH=/usr/local/pxf/bin:/usr/local/cloudberry-db/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

RUN make -C /tmp/cloudberry-pxf/external-table install \
    && make -C /tmp/cloudberry-pxf/cli/go/src/pxf-cli build \
    && mkdir -p /usr/local/pxf/bin \
    && cp /home/gpadmin/go/bin/pxf-cli /usr/local/pxf/bin/pxf-cli \
    && make -C /tmp/cloudberry-pxf/server install-server \
    && /usr/local/pxf/bin/pxf prepare

USER root
RUN rm -rf /tmp/cloudberry-pxf /tmp/cloudberry-pxf-checkout \
    && chown -R gpadmin:gpadmin /usr/local/pxf /home/gpadmin/pxf-base

COPY docker/cloudberry-pxf/start-with-pxf.sh /usr/local/bin/start-with-pxf.sh
RUN chmod 755 /usr/local/bin/start-with-pxf.sh

USER gpadmin
WORKDIR /home/gpadmin
CMD ["/usr/local/bin/start-with-pxf.sh"]
