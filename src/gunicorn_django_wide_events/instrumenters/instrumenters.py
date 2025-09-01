from collections import UserDict
from functools import wraps
from typing import Type

from gunicorn_django_wide_events.instrumenters.base import BaseInstrumenter


class InstrumenterRegistry(UserDict):
    def register(self, *, instrumenter: Type[BaseInstrumenter]) -> None:
        self.data[instrumenter.__name__] = instrumenter()


instrumenter_registry = InstrumenterRegistry()


def register_instrumenter(cls=None, *, registry=instrumenter_registry):
    @wraps(cls, updated=())
    def class_decorator(cls):
        registry.register(instrumenter=cls)

        return cls

    if cls:
        return class_decorator(cls)
    return class_decorator
