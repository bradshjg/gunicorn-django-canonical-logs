from gunicorn_django_wide_events.instrumenters import (  # noqa: F401 registers instrumenters
    request,
    exception,
    gunicorn_hooks,  # registers gunicorn hooks
    saturation,
)
