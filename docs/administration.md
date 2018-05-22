# Administration

## Monitoring

DCI is composed of four different parts :

- The database (PostgreSQL)
- The DCI api
- The DCI ui

The following are our recommendations about what to monitor for each and every component.

Note: The plugin column contain the name of the plugin used with the Sensu monitoring system - that is the one we use internally, please adapt accordingly based on your monitoring platform.

### Base

This applies for all nodes, independently of their roles.

| Service   | Plugin name  | Warning  | Critical | Check                             |
|-----------|--------------|----------|----------|-----------------------------------|
| Disk      | disk-checks  | 85%      | 95%      | check-disk-usage.rb -w 85 -c 95   |
| DNS       | dns          | N/A      | N/A      | check-dns.rb -d example.com       |
| Keepalive | N/A          | N/A      | N/A      | N/A                               |
| Load      | load-checks  | 5,5,5    | 10,10,10 | check-load.rb -w 5,5,5 -c 10,10,10 |
| Memory    | memory-checks | 85%      | 95%      | check-memory-percent.rb -w 85 -c 95  |
| NTP       | ntp          | 10       | 60       | check-ntp.rb -w 10 -c 60          |
| SSH       | network-checks | N/A      | N/A      | check-ports.rb -h 127.0.0.1 -p 22 -t 30 |

### PostgreSQL

| Service   | Plugin name  | Warning  | Critical | Check                             |
|-----------|--------------|----------|----------|-----------------------------------|
| PostgreSQL | network-checks | N/A      | N/A      | check-ports.rb -h 127.0.0.1 -p 5432 -t 30                           |

### DCI-API

| Service    | Plugin name | Warning | Critical | Check                              |
|------------|-------------|---------|---------|------------------------------------|
| DCI-API    | http        | N/A     | N/A     | check-http-json.rb -u http://example.com/api/v1             |

### DCI-UI

| Service      | Plugin name   | Warning  | Critical | Check                         |
|--------------|---------------|----------|----------|-------------------------------|
| DCI-UI       | http          | N/A      | N/A      | check-http.rb -u http://example.com              |


