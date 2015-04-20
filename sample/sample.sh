#!/usr/bin/bash

set -eux

DCI_CONTROL_SERVER=http://dci-boboa.rhcloud.com
# DCI_CONTROL_SERVER=http://127.0.0.1:5000

export DCI_CONTROL_SERVER

git push openshift master:master -f

curl -H "Content-Type: application/json" -X POST -d '[{"name": "father", "url": "http://127.0.0.1/environments/env-product1-generic//"}]' $DCI_CONTROL_SERVER/environments

environment_father_id=$(curl $DCI_CONTROL_SERVER/environments?where{"name":"father"}|jq '._items[0].id'|sed 's,",,g')

curl -H "Content-Type: application/json" -X POST -d '[{"name": "children", "url": "http://127.0.0.1/environments/env-product1-partner1/","environment_id":"'$environment_father_id'"}]' $DCI_CONTROL_SERVER/environments

environment_children_id=$(curl $DCI_CONTROL_SERVER/environments?where{"name":"father"}|jq '._items[0].id'|sed 's,",,g')

curl -H "Content-Type: application/json" -X POST -d '[{"name": "boa-2"}]' $DCI_CONTROL_SERVER/platforms

curl $DCI_CONTROL_SERVER/platforms?where{"name":"boa-2"}|jq '._items[0]'

curl $DCI_CONTROL_SERVER/platforms/boa-2|jq '.'
#

environment_id=$(curl $DCI_CONTROL_SERVER/environments?where{"name":"SPS-I.1.3-RH7.0-3nodes"}|jq '._items[0].id'|sed 's,",,g')
echo $environment_id

curl -H "Content-Type: application/json" -X POST -d '[{"environment_id":"'$environment_father_id'","struct":{"type":"gerrit","server":"softwarefactory.enovance.com","account":"goneri","gitsha1":"c5855449a73b423643571a1d77f017983909495d","port":29418}}]' $DCI_CONTROL_SERVER/notifications

curl -H "Content-Type: application/json" -X POST -d '[{"environment_id":"'$environment_children_id'","struct":{"type":"gerrit","server":"softwarefactory.enovance.com","account":"goneri","gitsha1":"c5855449a73b423643571a1d77f017983909495d","port":29418}}]' $DCI_CONTROL_SERVER/notifications

platform_id=$(curl "$DCI_CONTROL_SERVER/platforms?where{\"name\":\"boa-2\"}"|jq '._items[0].id'|sed 's,",,g')

client/dci_client.py auto $platform_id
client/dci_client.py auto $platform_id
