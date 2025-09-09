from __future__ import annotations

import time
from collections import defaultdict
from contextlib import contextmanager
from typing import ClassVar

from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.utils import CursorWrapper

from gunicorn_django_canonical_logs.event_context import Context
from gunicorn_django_canonical_logs.instrumenters.base import BaseInstrumenter
from gunicorn_django_canonical_logs.instrumenters.registry import register_instrumenter


class QueryCollector:
    _queries: ClassVar[dict[str, dict[str, int | float]]] = defaultdict(lambda: defaultdict(int))

    @classmethod
    def add(cls, sql: str, duration: float):
        cls._queries[sql]["count"] += 1
        cls._queries[sql]["duration"] += duration

    @classmethod
    def reset(cls):
        cls._queries.clear()

    @classmethod
    def get_data(cls):
        query_data = list(cls._queries.values())
        query_time = sum([query["duration"] for query in query_data])
        dup_query_data = [data for data in query_data if data["count"] > 1]
        dup_query_time = sum([query["duration"] for query in dup_query_data])

        return {
            "queries": sum([query["count"] for query in query_data]),
            "time": f"{query_time:.3f}",
            "dup_queries": sum([query["count"] for query in dup_query_data]),
            "dup_time": f"{dup_query_time:.3f}",
        }

    @classmethod
    @contextmanager
    def instrument(cls, sql):
        start = time.monotonic()
        try:
            yield
        finally:
            duration = time.monotonic() - start
            cls.add(sql, duration)


class InstrumenterCursorWrapper(CursorWrapper):
    def execute(self, sql, params=None):
        with QueryCollector.instrument(sql):
            return super().execute(sql, params)

    def executemany(self, sql, param_list):
        with QueryCollector.instrument(sql):
            return super().executemany(sql, param_list)


@register_instrumenter
class DatabaseInstrumenter(BaseInstrumenter):
    NAMESPACE = "db"

    def __init__(self):
        self._orig_make_cursor = BaseDatabaseWrapper.make_cursor

    def setup(self):
        BaseDatabaseWrapper.make_cursor = self._patched_make_cursor

    def teardown(self):
        BaseDatabaseWrapper.make_cursor = self._orig_make_cursor

    def call(self):
        Context.update(namespace=self.NAMESPACE, context=QueryCollector.get_data())
        QueryCollector.reset()

    @property
    def _patched_make_cursor(self):
        def _patched(self, cursor):
            return InstrumenterCursorWrapper(cursor, self)

        return _patched
