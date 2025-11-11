from __future__ import annotations

from collections import UserDict
from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import ValuesView

    from gunicorn_django_canonical_logs.instrumenters.protocol import InstrumenterProtocol


class InstrumenterRegistry(UserDict):
    def register(self, *, instrumenter: type[InstrumenterProtocol]) -> None:
        self.data[instrumenter.__name__] = instrumenter()

    def values(self) -> ValuesView[InstrumenterProtocol]:
        return self.data.values()


instrumenter_registry = InstrumenterRegistry()


def register_instrumenter(cls=None, *, registry=instrumenter_registry):
    @wraps(cls, updated=())
    def class_decorator(cls):
        registry.register(instrumenter=cls)

        return cls

    if cls:
        return class_decorator(cls)
    return class_decorator
