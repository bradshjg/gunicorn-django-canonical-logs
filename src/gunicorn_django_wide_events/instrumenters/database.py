import time

from django.db.backends.utils import CursorWrapper

from gunicorn_django_wide_events.event_context import Context
from gunicorn_django_wide_events.instrumenters.base import BaseInstrumenter
from gunicorn_django_wide_events.instrumenters.registry import register_instrumenter

NAMESPACE = "db"


@register_instrumenter
class DatabaseInstrumenter(BaseInstrumenter):
    NAMESPACE = "exc"

    def __init__(self):
        self._orig_execute = CursorWrapper.execute
        self._orig_executemany = CursorWrapper.executemany
        self.query_count = 0
        self.query_time = 0

    def setup(self):
        CursorWrapper.execute = self._patched_execute
        CursorWrapper.executemany = self._patched_executemany

    def teardown(self):
        CursorWrapper.execute = self._orig_execute
        CursorWrapper.executemany = self._orig_executemany

    def reset(self):
        self.query_count = 0
        self.query_time = 0

    def call(self):
        Context.update(
            namespace=NAMESPACE,
            context={
                "queries": self.query_count,
                "time": self.query_time,
            },
        )
        self.reset()

    @property
    def _patched_execute(instrumenter):  # noqa: N805
        def patch(self, sql, params=None):
            start_time = time.monotonic()
            res = instrumenter._orig_execute(self, sql, params)  # noqa: SLF001
            instrumenter.query_time += time.monotonic() - start_time
            instrumenter.query_count += 1
            return res

        return patch

    @property
    def _patched_executemany(instrumenter):  # noqa: N805
        def patch(self, sql, param_list):
            start_time = time.monotonic()
            res = instrumenter._orig_executemany(self, sql, param_list)  # noqa: SLF001
            instrumenter.query_time += time.monotonic() - start_time
            instrumenter.query_count += 1
            return res

        return patch
