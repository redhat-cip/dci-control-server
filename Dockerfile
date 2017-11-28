FROM centos:7

LABEL name="DCI CONTROL SERVER"
MAINTAINER DCI Team <distributed-ci@redhat.com>

RUN yum -y install epel-release && \
    yum -y install gcc && \
    yum -y install python python-pip python-devel && \
    yum -y install python34 python34-pip python34-devel && \
    yum clean all

RUN mkdir /opt/dci-control-server
WORKDIR /opt/dci-control-server
COPY requirements.txt /opt/dci-control-server/
RUN pip install --upgrade pip
RUN pip install tox
RUN pip install -r requirements.txt
COPY . /opt/dci-control-server/

EXPOSE 5000
ENV PYTHONPATH /opt/dci-control-server

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["python", "/opt/dci-control-server/bin/dci-runtestserver"]
