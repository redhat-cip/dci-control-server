import os

# Don't manage workers with gunicorn but by spawning more containers and let haproxy handle balancing
DEFAULT_NB_WORKERS = 1
workers = int(os.getenv("DCI_NB_WORKERS", DEFAULT_NB_WORKERS))
worker_connections = int(os.getenv("DCI_GUNICORN_WORKER_CONNECTIONS", 50))
worker_class = "gevent"

# Restart worker after a certain amount of requests to mitigate memory leaks, etc. …
if os.getenv("DCI_GUNICORN_MAX_REQUESTS") is not None:
    max_requests = int(os.getenv("DCI_GUNICORN_MAX_REQUESTS"))
# Add some jitter to avoid all workers restarting at the same time.
if os.getenv("DCI_GUNICORN_MAX_REQUESTS_JITTER") is not None:
    max_requests_jitter = int(os.getenv("DCI_GUNICORN_MAX_REQUESTS_JITTER"))

if os.getenv("DCI_GUNICORN_TIMEOUT") is not None:
    timeout = int(os.getenv("DCI_GUNICORN_TIMEOUT"))

if os.getenv("DCI_GUNICORN_GRACEFUL_TIMEOUT") is not None:
    graceful_timeout = int(os.getenv("DCI_GUNICORN_GRACEFUL_TIMEOUT"))

accesslog = "-"
access_log_format = (
    '%(h)s:%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
)
