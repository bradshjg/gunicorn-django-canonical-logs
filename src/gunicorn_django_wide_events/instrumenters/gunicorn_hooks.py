from gunicorn_django_wide_events.gunicorn_hooks.hooks import register_hook
from gunicorn_django_wide_events.instrumenters.instrumenters import instrumenter_registry
from gunicorn_django_wide_events.event_context import context


@register_hook
def post_worker_init(_):
    for instrumenter in instrumenter_registry.values():
        instrumenter.setup()

@register_hook
def pre_request(*_):
    context.reset()
