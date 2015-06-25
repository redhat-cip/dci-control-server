#!/bin/bash

set -eux

report_url="http://trunk.rdoproject.org/kilo/centos7/report.html"
#report_regex='s,.*\(.\{46\}_.\{8\}\)_\(.\{10\}\).*,http://trunk.rdoproject.org/kilo/centos7/\1/delorean-kilo.repo,'

# create a product
product_id=$(curl --user 'admin:admin' -H "Content-Type: application/json" -X POST -d '[{"name": "rdo-manager", "data": {"ksgen_args": {"provisioner":"manual", "product":"rdo", "product-version":"kilo", "product-version-repo":"delorean", "product-version-workaround": "rhel-7.0", "workarounds": "enabled", "distro": "centos-7.0", "installer": "rdo_manager", "installer-env": "virthost", "installer-topology": "minimal", "extra-vars": ["product.repo_type_override=none"]}}}]' ${DCI_CONTROL_SERVER}/products |jq '.id'|sed 's,",,g')
echo $product_id

# create a test
# TODO(Gonéri): Test disabled for the moment
test_id=$(curl --user 'admin:admin' -H "Content-Type: application/json" -X POST -d '[{"data": {"ksgen_args": {}}, "name":"khaleesi-tempest"}]' ${DCI_CONTROL_SERVER}/tests |jq '.id'|sed 's,",,g')
echo $test_id

lynx -dump ${report_url}|awk '/rpmbuild.log/ {print $2}'|sed "s,/rpmbuild.log,,"|sed "s,http://trunk.rdoproject.org/kilo/centos7/,,"| \
    while read url; do
	echo ${url}
        date=$(curl --head ${url}|grep Date|sed 's,Date: ,,'|sed 's/GMT.*//')

	# create a version
	json='[{"product_id": "'${product_id}'", "data": {"ksgen_args": {"extra-vars": ["product.repo.delorean_pin_version='${url}'", "product.repo.delorean.repo_file=delorean-kilo.repo"]}}, "name": "trunk-mgt-'${date}'"}]'
	echo ${json}
	ret=$(echo $json|curl --user 'admin:admin' -H 'Content-Type: application/json' --silent -X POST -d "${json}" ${DCI_CONTROL_SERVER}/versions)
	echo ${ret}|jq .
	version_id=$(echo ${ret}|jq -r '.id')

	echo "version_id: $version_id"

	# associate a test to a version
	test_version_id=$(curl --user 'admin:admin' -H 'Content-Type: application/json' --silent -X POST -d '[{"test_id": "'${test_id}'", "version_id": "'${version_id}'"}]' ${DCI_CONTROL_SERVER}/testversions |jq -r '.id')

	echo "test_version: ${test_version_id}"

	done
