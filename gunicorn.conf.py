import os

# Don't manage workers with gunicorn but by spawning more containers and let haproxy handle balancing
DEFAULT_NB_WORKERS = 1
workers = int(os.getenv("DCI_NB_WORKERS", DEFAULT_NB_WORKERS))
worker_connections = int(os.getenv("DCI_GUNICORN_WORKER_CONNECTIONS", 50))
worker_class = "gevent"

# Restart worker after a certain amount of requests to mitigate memory leaks, etc. …
max_requests = 1000
# Add some jitter to avoid all workers restarting at the same time.
max_requests_jitter = 250

accesslog = "-"
access_log_format = (
    '%(h)s:%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
)

# Some default values from gunicorn that might be of interest to tune
# max_connections = 1000
# backlog = 2048
# timeout = 30
# graceful_timeout = 30
