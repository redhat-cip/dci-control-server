#!/bin/bash
set -eux
PROJ_NAME=dci
DATE=$(date +%Y%m%d%H%M)
SHA=$(git rev-parse HEAD | cut -c1-8)


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
git archive HEAD --format=tgz --output=${HOME}/rpmbuild/SOURCES/${PROJ_NAME}-0.0.${DATE}git${SHA}.tgz
sed -i "s/VERS/${DATE}git${SHA}/g" ${HOME}/rpmbuild/SPECS/${PROJ_NAME}.spec
rpmbuild -bs ${HOME}/rpmbuild/SPECS/${PROJ_NAME}.spec

for arch in fedora-23-x86_64 epel-7-x86_64; do

    mkdir -p ${HOME}/.mock
    cp /etc/mock/${arch}.cfg ${HOME}/.mock/${arch}-with-extras.cfg

    if [[ "$arch" == "fedora-23-x86_64" ]]; then
        RPATH='fedora/23/x86_64'
    else
        RPATH='el/7/x86_64'
        sed -i '$i[elasticsearch-2.x]' ${HOME}/.mock/${arch}-with-extras.cfg
        sed -i '$iname=Elasticsearch repository for 2.x packages"' ${HOME}/.mock/${arch}-with-extras.cfg
        sed -i '$ibaseurl=http://packages.elastic.co/elasticsearch/2.x/centos' ${HOME}/.mock/${arch}-with-extras.cfg
        sed -i '$igpgcheck=0' ${HOME}/.mock/${arch}-with-extras.cfg
        sed -i '$ienabled=1' ${HOME}/.mock/${arch}-with-extras.cfg
        sed -i '$i[dci-extras]' ${HOME}/.mock/${arch}-with-extras.cfg
        sed -i '$iname=Distributed CI - No upstream package - CentOS 7"' ${HOME}/.mock/${arch}-with-extras.cfg
        sed -i '$ibaseurl=http://dci.enovance.com/repos/extras/el/7/x86_64/' ${HOME}/.mock/${arch}-with-extras.cfg
        sed -i '$igpgcheck=0' ${HOME}/.mock/${arch}-with-extras.cfg
        sed -i '$ienabled=1' ${HOME}/.mock/${arch}-with-extras.cfg
    fi

    # NOTE(spredzy) Add signing options
    #
    sed -i "\$aconfig_opts['plugin_conf']['sign_enable'] = True" ${HOME}/.mock/${arch}-with-extras.cfg
    sed -i "\$aconfig_opts['plugin_conf']['sign_opts'] = {}" ${HOME}/.mock/${arch}-with-extras.cfg
    sed -i "\$aconfig_opts['plugin_conf']['sign_opts']['cmd'] = 'rpmsign'" ${HOME}/.mock/${arch}-with-extras.cfg
    sed -i "\$aconfig_opts['plugin_conf']['sign_opts']['opts'] = '--addsign %(rpms)s'" ${HOME}/.mock/${arch}-with-extras.cfg

    # Build the RPMs in a clean chroot environment with mock to detect missing
    # BuildRequires lines.
    mkdir -p development
    mock -r ${HOME}/.mock/${arch}-with-extras.cfg rebuild --resultdir=development/${RPATH} ${HOME}/rpmbuild/SRPMS/${PROJ_NAME}*
done
