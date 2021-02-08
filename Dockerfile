FROM registry.access.redhat.com/ubi8/python-36

LABEL name="DCI API" version="0.1.0"
LABEL maintainer="DCI Team <distributed-ci@redhat.com>"

ENV LANG en_US.UTF-8

WORKDIR /opt/dci-control-server
COPY requirements.txt /opt/dci-control-server/

RUN pip install --no-cache-dir -U "pip<21.0" && \
    pip install --no-cache-dir -U tox && \
    pip install --no-cache-dir -r requirements.txt

COPY tests/data/ca.key tests/data/ca.crt /etc/ssl/repo/

ENV PYTHONPATH /opt/dci-control-server
ENV DISABLE_DB_START 1

EXPOSE 5000

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["python", "/opt/dci-control-server/bin/dci-runtestserver"]
