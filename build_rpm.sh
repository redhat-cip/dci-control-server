#!/bin/bash
set -eux
PROJ_NAME=dci
DATE=$(date +%Y%m%d%H%M)
SHA=$(git rev-parse HEAD | cut -c1-8)

declare -A repo_conf
repo_conf["fedora-23-x86_64"]='
[openstack-mitaka]
name=OpenStack Mitaka Repository
baseurl=http://mirror.centos.org/centos/7/cloud/$basearch/openstack-mitaka/
gpgcheck=1
enabled=1
gpgkey=https://raw.githubusercontent.com/openstack/puppet-openstack_extras/91fac8eab81d0ad071130887d72338a82c06a7f4/files/RPM-GPG-KEY-CentOS-SIG-Cloud
'
repo_conf["fedora-24-x86_64"]=${repo_conf["fedora-23-x86_64"]}
repo_conf["epel-7-x86_64"]='
[elasticsearch-2.x]
name="Elasticsearch repository for 2.x packages"
baseurl=http://packages.elastic.co/elasticsearch/2.x/centos
gpgcheck=1
enabled=1
gpgkey=https://packages.elastic.co/GPG-KEY-elasticsearch

[dci]
name=Distributed CI - CentOS 7
baseurl=https://packages.distributed-ci.io/repos/current/el/7/x86_64/
gpgcheck=1
gpgkey=https://packages.distributed-ci.io/RPM-GPG-KEY-distributedci
enabled=1

[dci-devel]
name="Distributed CI - Devel - CentOS 7"
baseurl=http://packages.distributed-ci.io/repos/development/el/7/x86_64/
gpgcheck=1
gpgkey=https://packages.distributed-ci.io/RPM-GPG-KEY-distributedci
enabled=1

[centos-openstack-mitaka]
name=CentOS-7 - OpenStack mitaka
baseurl=http://mirror.centos.org/centos/7/cloud/x86_64/openstack-mitaka/
gpgcheck=1
enabled=1
gpgkey=https://raw.githubusercontent.com/openstack/puppet-openstack_extras/91fac8eab81d0ad071130887d72338a82c06a7f4/files/RPM-GPG-KEY-CentOS-SIG-Cloud
'

# Configure rpmmacros to enable signing packages
#
echo '%_signature gpg' >> ~/.rpmmacros
echo '%_gpg_name Distributed-CI' >> ~/.rpmmacros

# Create the proper filesystem hierarchy to proceed with srpm creatioon
#
rm -rf ${HOME}/rpmbuild
mock --clean
rpmdev-setuptree
cp ${PROJ_NAME}.spec ${HOME}/rpmbuild/SPECS/
sed -i "s,__version__ = '\(.*\)',__version__ = '0.0.${DATE}git${SHA}'," dci/version.py
python setup.py sdist
cp -v dist/* ${HOME}/rpmbuild/SOURCES/
sed -i "s/VERS/${DATE}git${SHA}/g" ${HOME}/rpmbuild/SPECS/${PROJ_NAME}.spec
rpmbuild -bs ${HOME}/rpmbuild/SPECS/${PROJ_NAME}.spec

for arch in fedora-23-x86_64 fedora-24-x86_64 epel-7-x86_64; do
    rpath=$(echo ${arch}|sed s,-,/,g|sed 's,epel,el,')

    mkdir -p ${HOME}/.mock
    head -n -1 /etc/mock/${arch}.cfg > ${HOME}/.mock/${arch}-with-extras.cfg
    cat <<EOF >> ${HOME}/.mock/${arch}-with-extras.cfg
${repo_conf[${arch}]}
"""
# NOTE(spredzy) Add signing options
#
config_opts['plugin_conf']['sign_enable'] = True
config_opts['plugin_conf']['sign_opts'] = {}
config_opts['plugin_conf']['sign_opts']['cmd'] = 'rpmsign'
config_opts['plugin_conf']['sign_opts']['opts'] = '--addsign %(rpms)s'
config_opts['use_host_resolv'] = False
config_opts['files']['etc/hosts'] = """
127.0.0.1 pypi.python.org
"""
config_opts['nosync'] = True
EOF

    # Build the RPMs in a clean chroot environment with mock to detect missing
    # BuildRequires lines.
    mkdir -p development
    mock -r ${HOME}/.mock/${arch}-with-extras.cfg rebuild --resultdir=development/${rpath} ${HOME}/rpmbuild/SRPMS/${PROJ_NAME}*
done
