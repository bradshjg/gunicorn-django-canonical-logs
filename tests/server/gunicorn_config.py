from gunicorn_django_wide_events.glogging import Logger
from gunicorn_django_wide_events.registered_hooks import *  # noqa: F403 registers hooks

accesslog = "-"
logger_class = Logger
bind = ["127.0.0.1:8080"]
timeout = 30
workers = 1
