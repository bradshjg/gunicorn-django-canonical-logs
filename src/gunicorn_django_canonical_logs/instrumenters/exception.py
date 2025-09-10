from __future__ import annotations

import traceback
from typing import TYPE_CHECKING

from django.core.handlers import exception
from django.template.base import Node

from gunicorn_django_canonical_logs.event_context import Context
from gunicorn_django_canonical_logs.instrumenters.base import BaseInstrumenter
from gunicorn_django_canonical_logs.instrumenters.registry import register_instrumenter
from gunicorn_django_canonical_logs.stack_context import get_stack_loc_context

if TYPE_CHECKING:
    from types import TracebackType

    SysExcInfo = tuple[type[BaseException] | None, BaseException | None, TracebackType | None]

NAMESPACE = "exc"

_orig_handle_uncaught_exception = exception.handle_uncaught_exception


def _patched_handle_uncaught_exception(request, resolver, exc_info: SysExcInfo):
    exc_type, exc_value, tb = exc_info
    exc_context = {
        "type": exc_type.__name__,
        "msg": str(exc_value),
    }

    loc_context = get_stack_loc_context(traceback.extract_tb(tb))
    exc_context.update(loc_context)

    Context.update(namespace=NAMESPACE, context=exc_context)

    return _orig_handle_uncaught_exception(request, resolver, exc_info)


_orig_render_annotated = Node.render_annotated


def _patched_render_annotated(self, context):
    try:
        res = _orig_render_annotated(self, context)
    except Exception:
        Context.set("template", f"{context.template.name}:{self.token.lineno}", namespace=NAMESPACE)
        raise
    return res


@register_instrumenter
class ExceptionInstrumenter(BaseInstrumenter):
    def setup(self):
        exception.handle_uncaught_exception = _patched_handle_uncaught_exception
        Node.render_annotated = _patched_render_annotated

    def teardown(self):
        exception.handle_uncaught_exception = _orig_handle_uncaught_exception
        Node.render_annotated = _orig_render_annotated
