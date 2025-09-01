from gunicorn_django_wide_events.gunicorn_hooks.hooks import register_hook
from gunicorn_django_wide_events.instrumenters.instrumenters import instrumenter_registry


@register_hook
def post_worker_init(_):
    for instrumenter in instrumenter_registry.values():
        instrumenter.setup()
