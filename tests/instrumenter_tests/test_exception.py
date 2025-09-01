from typing import Generator
import pytest
import requests

from gunicorn_django_wide_events.event_context import context
from gunicorn_django_wide_events.instrumenters.exception import ExceptionInstrumenter

@pytest.fixture
def instrumenter() -> Generator[None, None, None]:
    context.reset()
    instrumenter = ExceptionInstrumenter()
    instrumenter.setup()
    yield
    instrumenter.teardown()


def test_sanity(instrumenter, live_server):
    resp = requests.get(live_server + "/view_exception/")
    assert resp.status_code == 500
