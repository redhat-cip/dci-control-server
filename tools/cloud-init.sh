#!/bin/bash
echo 'nameserver 8.8.4.4' > /etc/resolv.conf

yum distro-sync -y
yum install -y nodejs npm python-tox postgresql-server postgresql-devel postgresql-contrib python-devel python3-devel libffi-devel git python-simplejson
npm install jscs -g

# Start agent for 1 hour, then stop the node.
cat > /home/fedora/run.sh << 'EOF'
#!/bin/bash
[ -d dci-control-server ] || git clone https://github.com/enovance/dci-control-server
cd dci-control-server
start_date=$(date +%s)

while [ $(date +%s) -lt $((start_date+3600)) ]; do
    PYTHONPATH=. DCI_CONTROL_SERVER=https://stable-dcics.rhcloud.com/api DCI_LOGIN=partner DCI_PASSWORD=partner ./sample/tox-agent.py tox-agent-boa-$(hostname)
    PYTHONPATH=. DCI_CONTROL_SERVER=https://staging-dcics.rhcloud.com/api DCI_LOGIN=partner DCI_PASSWORD=partner ./sample/tox-agent.py tox-agent-boa-$(hostname)
    sleep 4
done
sudo halt
EOF
chown fedora:fedora /home/fedora/run.sh
chmod +x /home/fedora/run.sh
su - fedora /home/fedora/run.sh &
