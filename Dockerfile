FROM centos:7

LABEL name="DCI API" version="0.0.3"
LABEL maintainer="DCI Team <distributed-ci@redhat.com>"

ENV LANG en_US.UTF-8

WORKDIR /opt/dci-control-server
COPY requirements.txt /opt/dci-control-server/

RUN yum -y install epel-release && \
    yum -y install gcc git zeromq-devel \
    python python2-devel python2-pip python2-setuptools \
    python36 python36-devel python36-pip python36-setuptools && \
    yum clean all && \
    pip install --no-cache-dir -U "pip<21.0" && \
    pip install --no-cache-dir -U tox && \
    pip install --no-cache-dir -r requirements.txt

COPY tests/data/ca.key tests/data/ca.crt /etc/ssl/repo/

ENV PYTHONPATH /opt/dci-control-server
ENV DISABLE_DB_START 1

EXPOSE 5000

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["python", "/opt/dci-control-server/bin/dci-runtestserver"]
