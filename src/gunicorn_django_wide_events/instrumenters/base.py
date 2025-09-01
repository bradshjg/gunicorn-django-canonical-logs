from __future__ import annotations


class BaseInstrumenter:
    def setup(self) -> None:
        """Override to do any patching/configuration as necessary"""
        pass

    def teardown(self) -> None:
        """Override to revert any patching/configuration as necessary"""
        pass

    def call(self) -> None:
        """Override to add events to the context as necessary"""
        pass
