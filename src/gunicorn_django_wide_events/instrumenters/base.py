from __future__ import annotations

from abc import ABC, abstractmethod


class Instrumenter(ABC):
    @abstractmethod
    def setup():
        raise NotImplementedError

    @abstractmethod
    def call() -> dict[str, str]:
        """"""
        raise NotImplementedError
