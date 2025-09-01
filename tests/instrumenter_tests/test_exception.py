import re
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

    exc_context = context["exc"]

    assert exc_context["type"] == "MyError"
    assert exc_context["msg"] == "Oh noes!"

    assert re.match(r"app\.py:\d+:view_exception", exc_context["loc"])
    assert re.match(r"app\.py:\d+:func_that_throws", exc_context["cause_loc"])
