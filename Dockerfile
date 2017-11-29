FROM centos:7

LABEL name="DCI API" version="0.0.2"
MAINTAINER DCI Team <distributed-ci@redhat.com>

RUN yum -y --setopt=tsflags=nodocs install epel-release \
    https://packages.distributed-ci.io/dci-release.el7.noarch.rpm \
    centos-release-openstack-ocata && \
    yum-config-manager --save --setopt=centos-openstack-ocata.exclude=python-zmq,zeromq && \
    yum -y --setopt=tsflags=nodocs install dci-api && \
    yum -y install python-jwt python-dciauth && \
    yum clean all

WORKDIR /opt/dci-control-server
ENV PYTHONPATH /opt/dci-control-server
ENV DCI_SETTINGS_FILE /tmp/settings/settings.py

EXPOSE 5000

COPY bin/keycloak-provision.py /opt/keycloak-provision.py
COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["python", "/opt/dci-control-server/bin/dci-runtestserver"]
