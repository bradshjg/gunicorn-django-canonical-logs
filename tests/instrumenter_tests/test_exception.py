from typing import Generator

import pytest
import requests

from gunicorn_django_wide_events.event_context import context
from gunicorn_django_wide_events.instrumenters.exception import ExceptionInstrumenter


@pytest.fixture
def instrumenter() -> Generator[ExceptionInstrumenter, None, None]:
    context.reset()
    instrumenter = ExceptionInstrumenter()
    instrumenter.setup()
    yield instrumenter
    instrumenter.teardown()


@pytest.mark.usefixtures("instrumenter")
def test_view_exception(live_server):
    url = live_server + "/view_exception/"
    resp = requests.get(url)
    assert resp.status_code == 500
    log_str = str(context)
    assert "exc_type=MyError" in log_str
    assert 'exc_msg="Oh noes!"' in log_str
