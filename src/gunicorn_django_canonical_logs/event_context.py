from __future__ import annotations

from collections import defaultdict
from typing import Any


class EventContext:
    DEFAULT_NAMESPACE = "app"

    def __init__(self):
        self._context = defaultdict(dict)

    def get(self, key: str, *, namespace: str = DEFAULT_NAMESPACE) -> Any:
        return self._context[namespace].get(key)

    def set(self, key: str, val: Any, *, namespace: str = DEFAULT_NAMESPACE) -> None:
        self._context[namespace][key] = val

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
