from gunicorn_django_canonical_logs.glogging import Logger
from gunicorn_django_canonical_logs.gunicorn_hooks import *  # noqa: F403 registers hooks

pythonpath = "tests/server"
raw_env = ["DJANGO_SETTINGS_MODULE=settings"]
accesslog = "-"
logger_class = Logger
bind = ["127.0.0.1:8080"]
timeout = 1
workers = 1
