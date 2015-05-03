#!/bin/bash

set -eux

#DCI_CONTROL_SERVER=http://dci-boboa.rhcloud.com
DCI_CONTROL_SERVER=http://127.0.0.1:5000

export DCI_CONTROL_SERVER

#git push openshift master:master -f


# create a remote ci
remoteci_id=$(curl -H "Content-Type: application/json" -X POST -d '[{"name": "rhci"}]' ${DCI_CONTROL_SERVER}/remotecis |jq '.id'|sed 's,",,g')

echo $remoteci_id

# create a product
product_id=$(curl -H "Content-Type: application/json" -X POST -d '[{"name": "rhel-osp", "data": {}}]' ${DCI_CONTROL_SERVER}/products |jq '.id'|sed 's,",,g')

echo $product_id

# create a version
version_id=$(curl -H "Content-Type: application/json" -X POST -d '[{"product_id": "'${product_id}'", "data": {}, "name": "version7"}]' ${DCI_CONTROL_SERVER}/versions |jq '.id'|sed 's,",,g')

echo $version_id

# create a test
test_id=$(curl -H "Content-Type: application/json" -X POST -d '[{"data": {}, "name":"tempest"}]' ${DCI_CONTROL_SERVER}/tests |jq '.id'|sed 's,",,g')

echo $test_id


# associate a test to a version
test_version_id=$(curl -H "Content-Type: application/json" -X POST -d '[{"test_id": "'${test_id}'", "version_id": "'${version_id}'"}]' ${DCI_CONTROL_SERVER}/testversions |jq '.id'|sed 's,",,g')

# get a job

job=$(curl http://127.0.0.1:5000/jobs/get_job_by_remoteci/${remoteci_id})

echo ${job}
