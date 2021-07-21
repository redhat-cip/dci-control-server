FROM centos:7

LABEL name="DCI API" version="0.0.3"
LABEL maintainer="DCI Team <distributed-ci@redhat.com>"

ENV LANG en_US.UTF-8

WORKDIR /opt/dci-control-server
COPY dci-control-server.spec /opt/dci-control-server/

RUN set -x; yum -y install epel-release centos-release-openstack-rocky https://packages.distributed-ci.io/dci-release.el7.noarch.rpm && \
    echo -e "[dci-extras]\nname=DCI Extras YUM repo\nbaseurl=https://packages.distributed-ci.io/repos/extras/el/\$releasever/\$basearch/\nenabled=1\ngpgcheck=0" > /etc/yum.repos.d/dci-extras.repo && \
    yum update -y && \
    yum -y install rpm-build gcc && \
    yum -y install $(rpmspec -q --requires -E '%define rhel 7' dci-control-server.spec|grep -v systemd) && \
    rpm -q $(rpmspec -q --requires -E '%define rhel 7' dci-control-server.spec|grep -v systemd) && \
    yum -y install python python2-devel python2-pip python2-setuptools && \
    yum -y install python36 python36-devel python36-pip python36-setuptools && \
    yum -y install centos-release-scl && \
    yum -y install rh-postgresql96 rh-postgresql96-postgresql-contrib rh-postgresql96-postgresql-devel && \
    yum clean all && \
    python3 -m pip install --upgrade tox

COPY tests/data/ca.key tests/data/ca.crt /etc/ssl/repo/

ENV PYTHONPATH /opt/dci-control-server
ENV DISABLE_DB_START 1

EXPOSE 5000

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["python", "/opt/dci-control-server/bin/dci-runtestserver"]
