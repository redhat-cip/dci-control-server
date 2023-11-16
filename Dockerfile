FROM registry.access.redhat.com/ubi8/ubi-minimal
LABEL name="DCI API" version="0.1.0"
LABEL maintainer="DCI Team <distributed-ci@redhat.com>"

COPY . /opt/dci-control-server

COPY entrypoint.sh /usr/local/sbin/
COPY gunicorn.conf.py /etc/

WORKDIR /opt/dci-control-server

RUN microdnf update && \
    microdnf -y install python3-pip python3-wheel && \
    microdnf -y install python3-devel gcc postgresql-devel && \
    pip3 --no-cache-dir install -r requirements.txt && \
    pip3 --no-cache-dir install --editable . && \
    microdnf -y remove python3-devel gcc postgresql-devel && \
    microdnf -y clean all

EXPOSE 5000

ENTRYPOINT ["/usr/local/sbin/entrypoint.sh"]

CMD ["/usr/local/bin/gunicorn", "-c", "/etc/gunicorn.conf.py", "-b", "0.0.0.0:5000", "dci.app:create_app()"]
