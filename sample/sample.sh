#!/usr/bin/bash

set -eux

DCI_CONTROL_SERVER=http://dci-boboa.rhcloud.com
# DCI_CONTROL_SERVER=http://127.0.0.1:5000

export DCI_CONTROL_SERVER

git push openshift master:master -f

curl -H "Content-Type: application/json" -X POST -d '[{"name": "SPS-I.1.3-RH7.0-3nodes", "url": "http://boa-2/environments/13758242/"}]' $DCI_CONTROL_SERVER/environments

curl -H "Content-Type: application/json" -X POST -d '[{"name": "boa-2"}]' $DCI_CONTROL_SERVER/platforms

curl $DCI_CONTROL_SERVER/platforms?where{"name":"boa-2"}|jq '._items[0]'

curl $DCI_CONTROL_SERVER/platforms/boa-2|jq '.'
#
curl $DCI_CONTROL_SERVER/environments?where{"name":"SPS-I.1.3-RH7.0-3nodes"}|jq '.'
environment_id=$(curl $DCI_CONTROL_SERVER/environments?where{"name":"SPS-I.1.3-RH7.0-3nodes"}|jq '._items[0].id'|sed 's,",,g')
echo $environment_id

curl -H "Content-Type: application/json" -X POST -d '[{"environment_id":"'$environment_id'","struct":{"type":"gerrit","server":"softwarefactory.enovance.com","account":"goneri","gitsha1":"e743be58a962f971a613f76daf1e304f0bc2d02a","port":29418}}]' $DCI_CONTROL_SERVER/notifications


platform_id=$(curl "$DCI_CONTROL_SERVER/platforms?where{\"name\":\"boa-2\"}"|jq '._items[0].id'|sed 's,",,g')

client/dci_client.py auto $platform_id
