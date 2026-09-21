import os

bind = '0.0.0.0:8000'
workers = int(os.getenv('WEB_CONCURRENCY', '4'))

worker_class = 'uvicorn.workers.UvicornWorker'

forwarded_allow_ips = '*'
proxy_protocol = False

accesslog = '-'
errorlog = '-'
loglevel = 'info'

timeout = 60
graceful_timeout = 30
keepalive = 5
