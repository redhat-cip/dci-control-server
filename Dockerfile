FROM registry.access.redhat.com/ubi8/ubi

LABEL name="DCI API" version="0.1.0"
LABEL maintainer="DCI Team <distributed-ci@redhat.com>"

ENV LANG en_US.UTF-8

WORKDIR /opt/dci-control-server

COPY . /opt/dci-control-server/

RUN yum install --disableplugin=subscription-manager -y httpd python36 python36-devel gcc gcc-c++ python3-mod_wsgi

RUN pip3 install --no-cache-dir -U "pip<21.0" && \
    pip3 install --no-cache-dir jinja2-cli && \
    pip3 install --no-cache-dir -r requirements.txt

COPY tests/data/ca.key tests/data/ca.crt /etc/ssl/repo/
COPY conf/vhost.j2 /etc/httpd/vhost.conf

ENV PYTHONPATH /opt/dci-control-server
ENV DISABLE_DB_START 1

EXPOSE 5000

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

CMD ["apachectl", "-DFOREGROUND"]
