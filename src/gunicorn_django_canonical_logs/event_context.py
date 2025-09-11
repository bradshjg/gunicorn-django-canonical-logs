from __future__ import annotations

import time
from collections import defaultdict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Generator


class EventContext:
    DEFAULT_NAMESPACE = "app"

    def __init__(self):
        self._context = defaultdict(dict)

    def get(self, key: str, *, namespace: str = DEFAULT_NAMESPACE) -> Any:
        return self._context[namespace].get(key)

    def set(self, key: str, val: Any, *, namespace: str = DEFAULT_NAMESPACE) -> None:
        self._context[namespace][key] = val

    @contextmanager
    def time(self, key: str, *, namespace: str = DEFAULT_NAMESPACE) -> Generator[None, None, None]:
        key = f"{key}_time"
        try:
            current_timing = float(self.get(key, namespace=namespace))
        except (TypeError, ValueError):  # overrides value if it's not parseable as a float
            current_timing = 0
            self.set(key, current_timing, namespace=namespace)
        start = time.monotonic()
        try:
            yield
        finally:
            timing = time.monotonic() - start
            current_timing += timing
            self.set(key, f"{current_timing:.3f}", namespace=namespace)

    def update(self, *, context: dict[str, Any], namespace: str = DEFAULT_NAMESPACE, beginning: bool = False) -> None:
        self._context[namespace].update(context)
        if beginning:
            reordered = {namespace: self._context.pop(namespace), **self._context}
            self._context = defaultdict(dict, reordered)

    def raw_items(self):
        return self._context.items()

    def reset(self) -> None:
        self._context = defaultdict(dict)


Context = EventContext()
