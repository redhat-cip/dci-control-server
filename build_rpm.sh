#!/bin/bash
set -eux
PROJ_NAME=dci
DATE=$(date +%Y%m%d%H%M)
SHA=$(git rev-parse HEAD | cut -c1-8)

# Create the proper filesystem hierarchy to proceed with srpm creatioon
#
#
rm -rf ${HOME}/rpmbuild
mock --clean
rpmdev-setuptree
cp ${PROJ_NAME}.spec ${HOME}/rpmbuild/SPECS/
git archive master --format=tgz --output=${HOME}/rpmbuild/SOURCES/${PROJ_NAME}-0.0.${DATE}git${SHA}.tgz
sed -i "s/VERS/${DATE}git${SHA}/g" ${HOME}/rpmbuild/SPECS/${PROJ_NAME}.spec
rpmbuild -bs ${HOME}/rpmbuild/SPECS/${PROJ_NAME}.spec

# NOTE(spredzy): Include the elasticsearch repo in mock env
#
mkdir -p ${HOME}/.mock
arch=epel-7-x86_64
cp /etc/mock/${arch}.cfg ${HOME}/.mock/${arch}-with-es.cfg
sed -i '$i[elasticsearch-2.x]' ${HOME}/.mock/${arch}-with-es.cfg
sed -i '$iname=Elasticsearch repository for 2.x packages"' ${HOME}/.mock/${arch}-with-es.cfg
sed -i '$ibaseurl=http://packages.elastic.co/elasticsearch/2.x/centos' ${HOME}/.mock/${arch}-with-es.cfg
sed -i '$igpgcheck=0' ${HOME}/.mock/${arch}-with-es.cfg
sed -i '$ienabled=1' ${HOME}/.mock/${arch}-with-es.cfg


# Build the RPMs in a clean chroot environment with mock to detect missing
# BuildRequires lines.
RPATH='el/7/x86_64'
mkdir -p development
mock -r ${HOME}/.mock/${arch}-with-es.cfg rebuild --resultdir=development/${RPATH} ${HOME}/rpmbuild/SRPMS/${PROJ_NAME}*
