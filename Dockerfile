FROM centos:7

LABEL name="DCI CONTROL SERVER"
MAINTAINER DCI Team <distributed-ci@redhat.com>

RUN yum -y install epel-release && \
    yum -y install python python-devel python-tox python2-pip && \
    yum clean all

RUN mkdir /opt/dci-control-server
WORKDIR /opt/dci-control-server
COPY requirements.txt /opt/dci-control-server/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . /opt/dci-control-server/

EXPOSE 5000
ENV PYTHONPATH /opt/dci-control-server

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["python", "/opt/dci-control-server/bin/dci-runtestserver"]
