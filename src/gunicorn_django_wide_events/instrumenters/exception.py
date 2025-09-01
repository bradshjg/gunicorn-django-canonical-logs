from __future__ import annotations

import os
import sys
import sysconfig
import traceback
from typing import TYPE_CHECKING, Optional

from django.core.handlers import exception

from gunicorn_django_wide_events.event_context import context
from gunicorn_django_wide_events.instrumenters.base import BaseInstrumenter
from gunicorn_django_wide_events.instrumenters.instrumenters import register_instrumenter

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

            exc_context.update(self.get_exc_loc_context(tb))

            context["exc"] = exc_context

            return self._orig_handle_uncaught_exception(request, resolver, exc_info)

        exception.handle_uncaught_exception = patched_handle_uncaught_exception

    def teardown(self):
        exception.handle_uncaught_exception = self._orig_handle_uncaught_exception

    def call(self):
        pass

    def filter_stack_summary(self, stack_summaries: traceback.StackSummary) -> list[traceback.FrameSummary]:
        library_paths = sysconfig.get_paths().values()
        return [
            frame_summary
            for frame_summary in stack_summaries
            if not any(frame_summary.filename.startswith((path, os.path.realpath(path))) for path in library_paths)
        ]

    def format_frame_summary(self, frame_summary: traceback.FrameSummary) -> str:
        # use sys.path to find the shortest possible import (i.e. strip base project path)
        python_paths = sorted(sys.path, key=len, reverse=True)
        fname = frame_summary.filename
        for path in python_paths:
            if fname.startswith(path):
                to_remove = path if path.endswith("/") else path + "/"
                fname = fname.removeprefix(to_remove)
                break

        return f"{fname}:{frame_summary.lineno}:{frame_summary.name}"

    def get_exc_loc_context(self, tb: TracebackType):
        stack_summary = traceback.extract_tb(tb)
        filtered_frame_summaries = self.filter_stack_summary(stack_summary)

        if not filtered_frame_summaries:
            # only library code in the stack, use the last frame
            return {"loc": self.format_frame_summary(stack_summary[-1])}

        if len(filtered_frame_summaries) == 1:
            # cause was in library code
            return {
                "loc": self.format_frame_summary(filtered_frame_summaries[0]),
                "cause_loc": self.format_frame_summary(stack_summary[-1]),
            }

        return {
            "loc": self.format_frame_summary(filtered_frame_summaries[0]),
            "cause_loc": self.format_frame_summary(filtered_frame_summaries[-1]),
        }
