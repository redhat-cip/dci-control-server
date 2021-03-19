FROM centos:7

LABEL name="DCI API" version="0.0.3"
LABEL maintainer="DCI Team <distributed-ci@redhat.com>"

ENV LANG en_US.UTF-8

WORKDIR /opt/dci-control-server
COPY requirements.txt /opt/dci-control-server/

RUN set -x; yum -y install epel-release centos-release-openstack-train && \
    yum -y install https://packages.distributed-ci.io/dci-release.el7.noarch.rpm && \
    yum -y install dci-control-server && \
    rpm -e dci-control-server

COPY tests/data/ca.key tests/data/ca.crt /etc/ssl/repo/

ENV PYTHONPATH /opt/dci-control-server
ENV DISABLE_DB_START 1

EXPOSE 5000

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["python", "/opt/dci-control-server/bin/dci-runtestserver"]
