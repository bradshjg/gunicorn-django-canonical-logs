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
    assert context["w_num"] == 0
    assert context["w_active"] == 0
    assert context["backlog"] == 0
