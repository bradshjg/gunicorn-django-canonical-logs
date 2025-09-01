from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.handlers import exception

from gunicorn_django_wide_events.event_context import context
from gunicorn_django_wide_events.instrumenters.base import BaseInstrumenter
from gunicorn_django_wide_events.instrumenters.instrumenters import register_instrumenter

if TYPE_CHECKING:
    from types import TracebackType


@register_instrumenter
class ExceptionInstrumenter(BaseInstrumenter):
    def setup(self):
        _orig_handle_uncaught_exception = exception.handle_uncaught_exception

        def patched_handle_uncaught_exception(
            request, resolver, exc_info: tuple[type[Exception], Exception, TracebackType]
        ):
            context["exc"] = {
                "type": exc_info[0].__name__,
                "msg": exc_info[1].args[0],
            }
            return _orig_handle_uncaught_exception(request, resolver, exc_info)

        exception.handle_uncaught_exception = patched_handle_uncaught_exception

    def call(self):
        pass
