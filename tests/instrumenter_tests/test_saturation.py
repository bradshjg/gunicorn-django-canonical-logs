from typing import Generator

import pytest

from gunicorn_django_wide_events.event_context import context
from gunicorn_django_wide_events.instrumenters.saturation import SaturationInstrumenter


@pytest.fixture
def instrumenter() -> Generator[SaturationInstrumenter, None, None]:
    context.reset()
    instrumenter = SaturationInstrumenter()
    instrumenter.setup()
    yield instrumenter
    instrumenter.teardown()


def test_adds_context_on_call(instrumenter):
    instrumenter.call()
    log_str = str(context)
    assert "w_num=0" in log_str
    assert "w_active=0" in log_str
    assert "backlog=0" in log_str
