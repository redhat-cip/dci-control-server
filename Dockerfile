FROM centos:stream8

LABEL name="DCI API" version="0.0.3"
LABEL maintainer="DCI Team <distributed-ci@redhat.com>"

ENV LANG en_US.UTF-8

WORKDIR /opt/dci-control-server
COPY dci-control-server.spec /opt/dci-control-server/

RUN dnf -y install epel-release centos-release-openstack-train https://packages.distributed-ci.io/dci-release.el8.noarch.rpm && \
    echo -e "[dci-extras]\nname=DCI Extras YUM repo\nbaseurl=https://packages.distributed-ci.io/repos/extras/el/\$releasever/\$basearch/\nenabled=1\ngpgcheck=0" > /etc/yum.repos.d/dci-extras.repo && \
    dnf update -y && \
    dnf -y install rpm-build gcc && \
    dnf -y install $(rpmspec -q --requires -E '%define rhel 8' dci-control-server.spec|grep -v systemd) && \
    rpm -q $(rpmspec -q --requires -E '%define rhel 8' dci-control-server.spec|grep -v systemd) && \
    dnf -y install python36 python36-devel python3-pip python3-setuptools python3-tox && \
    dnf module enable -y postgresql:9.6 && \
    dnf -y install postgresql postgresql-contrib postgresql-devel && \
    dnf clean all

COPY sso/ca.key /etc/ssl/repo/
COPY sso/ca.crt /etc/ssl/repo/
COPY sso/RH-IT-Root-CA.crt /etc/pki/ca-trust/source/anchors/RH-IT-Root-CA.crt
RUN update-ca-trust

ENV PYTHONPATH /opt/dci-control-server
ENV DISABLE_DB_START 1

EXPOSE 5000

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["python3", "/opt/dci-control-server/bin/dci-runtestserver"]
