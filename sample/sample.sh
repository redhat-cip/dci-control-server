#!/usr/bin/bash


export DCI_CONTROL_SERVER=http://dci-boboa.rhcloud.com
#DCI_CONTROL_SERVER=http://127.0.0.1:5000

git push openshift master:master -f


curl -H "Content-Type: application/json" -X POST -d '[{"name": "SPS-I.1.3-RH7.0-3nodes", "url": "http://boa-2/environments/13758242/"}]' $DCI_CONTROL_SERVER/environments


curl -H "Content-Type: application/json" -X POST -d @sample-scenario.json $DCI_CONTROL_SERVER/scenarios

curl -H "Content-Type: application/json" -X POST -d '[{"name": "boa-2"}]' $DCI_CONTROL_SERVER/platforms

curl 'http://dci-boboa.rhcloud.com/platforms?where{"name":"boa-2"}'|jq '._items[0]'

curl 'http://dci-boboa.rhcloud.com/platforms/boa-2'|jq '.'

platform_id=$(curl 'http://dci-boboa.rhcloud.com/platforms?where{"name":"boa-2"}'|jq '._items[0].id'|sed 's,",,')

client/dci_client.py auto $platform_id

curl http://$DCI_CONTROL_SERVER.com/jobstates|jq '._items'
