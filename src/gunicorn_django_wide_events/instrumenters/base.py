from __future__ import annotations

from abc import ABC, abstractmethod


class BaseInstrumenter(ABC):
    @abstractmethod
    def setup(self):
        """Override to do any patching/configuration necessary"""
        raise NotImplementedError

    @abstractmethod
    def call(self) -> dict[str, str]:
        """Override to add events to the context"""
        raise NotImplementedError
