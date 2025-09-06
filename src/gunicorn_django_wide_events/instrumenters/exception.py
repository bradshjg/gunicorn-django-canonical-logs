from __future__ import annotations

import traceback
from typing import TYPE_CHECKING, Optional

from django.core.handlers import exception

from gunicorn_django_wide_events.event_context import context
from gunicorn_django_wide_events.instrumenters.base import BaseInstrumenter
from gunicorn_django_wide_events.instrumenters.instrumenters import register_instrumenter
from gunicorn_django_wide_events.stack_context import get_stack_loc_context

if TYPE_CHECKING:
    from types import TracebackType

    from django.core.handlers.wsgi import WSGIRequest
    from django.urls.resolvers import URLResolver

    SysExcInfo = tuple[Optional[type[BaseException]], Optional[BaseException], Optional[TracebackType]]


@register_instrumenter
class ExceptionInstrumenter(BaseInstrumenter):
    def __init__(self):
        self._orig_handle_uncaught_exception = exception.handle_uncaught_exception

    def setup(self):
        def patched_handle_uncaught_exception(request: WSGIRequest, resolver: URLResolver, exc_info: SysExcInfo):
            exc_type, exc_value, tb = exc_info
            exc_context = {
                "type": exc_type.__name__,
                "msg": str(exc_value),
            }

            loc_context = get_stack_loc_context(traceback.extract_tb(tb))
            exc_context.update(loc_context)

            context["exc"] = exc_context

            return self._orig_handle_uncaught_exception(request, resolver, exc_info)

        exception.handle_uncaught_exception = patched_handle_uncaught_exception

    def teardown(self):
        exception.handle_uncaught_exception = self._orig_handle_uncaught_exception

    def call(self):
        pass
