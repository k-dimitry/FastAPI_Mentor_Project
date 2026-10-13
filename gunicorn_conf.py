import os

bind = '0.0.0.0:8000'
workers = int(os.getenv('WEB_CONCURRENCY', '4'))

worker_class = 'uvicorn.workers.UvicornWorker'

# Не '*': клиент подменит X-Forwarded-For и получит новый счётчик
# анонимного rate limit. 127.0.0.1 — прокси, который коннектится
# к gunicorn напрямую. В Docker задайте IP, с которого виден прокси.
forwarded_allow_ips = os.getenv('FORWARDED_ALLOW_IPS', '127.0.0.1')
proxy_protocol = False

accesslog = '-'
errorlog = '-'
loglevel = 'info'

timeout = 60
graceful_timeout = 30
keepalive = 5
