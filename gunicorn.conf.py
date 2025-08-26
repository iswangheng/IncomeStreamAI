# Gunicorn configuration file
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000

# Timeout settings - 增加超时时间以支持OpenAI API慢响应
timeout = 300  # 5分钟超时，足够处理最慢的OpenAI请求
keepalive = 5

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Preload application code before the worker processes are forked
preload_app = True

# Restart workers when code changes (for development)
reload = True

# Enable reuse of port
reuse_port = True

# Logging
loglevel = "info"
accesslog = "-"  # Log to stdout
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'