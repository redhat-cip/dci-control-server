FROM registry.access.redhat.com/ubi8/ubi-minimal
LABEL name="DCI API" version="0.1.0"
LABEL maintainer="DCI Team <distributed-ci@redhat.com>"

COPY sso/RH-IT-Root-CA.crt /etc/pki/ca-trust/source/anchors/RH-IT-Root-CA.crt
RUN update-ca-trust

WORKDIR /opt/dci-control-server

# install dependencies first
COPY requirements.txt setup.py /opt/dci-control-server/

RUN microdnf update && \
  microdnf -y install python3-pip python3-wheel && \
  microdnf -y install python3-devel gcc postgresql-devel && \
  pip3 --no-cache-dir install -r requirements.txt && \
  microdnf -y remove python3-devel gcc postgresql-devel && \
  microdnf -y clean all

# install source after
COPY entrypoint-devenv.sh entrypoint.sh /usr/local/sbin/
COPY gunicorn.conf.py /etc/

COPY . /opt/dci-control-server/

RUN pip3 --no-cache-dir install --editable .

EXPOSE 5000

ENTRYPOINT ["/usr/local/sbin/entrypoint.sh"]

CMD ["/usr/local/bin/gunicorn", "-c", "/etc/gunicorn.conf.py", "-b", "0.0.0.0:5000", "dci.app:create_app()"]
