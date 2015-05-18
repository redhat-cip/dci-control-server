#!/bin/bash
#
# Copyright 2015 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

DCI_CONTROL_SERVER=${DCI_CONTROL_SERVER:-'https://stable-dcics.rhcloud.com/api'}
ADMIN_PASSWORD=${ADMIN_PASSWORD,-'admin'}
CURL="curl --user 'admin:admin' -H 'Content-Type: application/json' --silent"
set -eux

report_url="http://trunk-mgt.rdoproject.org/repos/report.html"
report_regex='s,.*\(.\{46\}_.\{8\}\)_\(.\{10\}\).*,http://trunk-mgt.rdoproject.org/repos/\1 \2,'

curl --user 'admin:admin' -X DELETE ${DCI_CONTROL_SERVER}/products
curl --user 'admin:admin' -X DELETE ${DCI_CONTROL_SERVER}/jobs

# create a remote ci
remoteci_id=$(curl --user 'admin:admin' -H 'Content-Type: application/json' --silent -X POST -d '[{"name": "rhci"}]' ${DCI_CONTROL_SERVER}/remotecis |jq -r '.id')

echo "remoteci_id: $remoteci_id"

# create a product
product_id=$(curl --user 'admin:admin' -H 'Content-Type: application/json' --silent -X POST -d '[{"name": "packstack-rdo", "data": {"ksgen_args": {"rules-file": "%%KHALEESI_SETTINGS%%/rules/packstack-rdo-aio.yml"}}}]' ${DCI_CONTROL_SERVER}/products |jq -r '.id')

echo "product_id: $product_id"

# create a test
test_id=$(curl --user 'admin:admin' -H 'Content-Type: application/json' --silent -X POST -d '[{"data": {"ksgen_args": {"provisioner-options": "execute_provision", "product-version-workaround": "centos-7.0", "provisioner": "openstack", "distro": "centos-7.0", "tester": "tempest", "installer-network-variant": "ml2-vxlan", "product-version": "kilo", "tester-setup": "rpm", "installer-network": "neutron", "tester-tests": "all", "product-version-repo": "delorean", "workarounds": "enabled"}}, "name":"centos-7.0"}]' ${DCI_CONTROL_SERVER}/tests |jq -r '.id')

echo "test_id: $test_id"

lynx -dump ${report_url}|awk '/rpmbuild.log/ {print $2}'|sed "${report_regex}"| \
    while read url date; do
	echo ${url} ${date}

	# create a version
	json='[{"product_id": "'${product_id}'", "data": {"ksgen_args": {"extra-vars": {"product.repo.delorean_mgt_pin_version": "'${url}'", "product.repo.delorean_pin_version": "'${url}'", "product.repo.delorean.repo_file": "delorean.repo"}}}, "name": "trunk-mgt-'${date}'"}]'
	echo ${json}
	# curl --user 'admin:admin' -H 'Content-Type: application/json' --silent -X POST -d "${json}" ${DCI_CONTROL_SERVER}/versions
	ret=$(echo $json|curl --user 'admin:admin' -H 'Content-Type: application/json' --silent -X POST -d "${json}" ${DCI_CONTROL_SERVER}/versions)
	echo ${ret}|jq .
	version_id=$(echo ${ret}|jq -r '.id')

	echo "version_id: $version_id"

	# associate a test to a version
	test_version_id=$(curl --user 'admin:admin' -H 'Content-Type: application/json' --silent -X POST -d '[{"test_id": "'${test_id}'", "version_id": "'${version_id}'"}]' ${DCI_CONTROL_SERVER}/testversions |jq -r '.id')

	echo "test_version: ${test_version_id}"

	done
