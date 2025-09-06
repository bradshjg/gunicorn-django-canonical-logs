from gunicorn_django_wide_events.event_context import Context
from gunicorn_django_wide_events.gunicorn_hooks import register_hook
from gunicorn_django_wide_events.instrumenters import (  # noqa: F401 registers instrumenters
    exception,
    request,
    saturation,
)
from gunicorn_django_wide_events.instrumenters.registry import instrumenter_registry


@register_hook
def post_fork(_server, _worker):
    for instrumenter in instrumenter_registry.values():
        instrumenter.setup()


@register_hook
def pre_request(_worker, _req):
    Context.reset()
