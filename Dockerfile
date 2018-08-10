FROM centos:7

LABEL name="DCI API" version="0.0.2"
LABEL maintainer="DCI Team <distributed-ci@redhat.com>"

ENV LANG en_US.UTF-8

RUN yum -y install epel-release && \
    yum -y install gcc git zeromq-devel \
    python python2-devel python2-pip python2-setuptools \
    python34 python34-devel python34-pip python34-setuptools && \
    yum clean all

RUN pip install -U pip
# python-tox is broken, install tox with pip instead
RUN pip install -U tox

WORKDIR /opt/dci-control-server
ADD requirements.txt /opt/dci-control-server/
RUN pip install -r requirements.txt
ADD . /opt/dci-control-server/

COPY tests/data/ca.key /etc/ssl/repo/ca.key
COPY tests/data/ca.crt /etc/ssl/repo/ca.crt

ENV PYTHONPATH /opt/dci-control-server
ENV DISABLE_DB_START 1

EXPOSE 5000

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["python", "/opt/dci-control-server/bin/runtestserver"]
