import re
from typing import Generator

import pytest
import requests

from gunicorn_django_wide_events.event_context import Context
from gunicorn_django_wide_events.instrumenters.exception import ExceptionInstrumenter


@pytest.fixture
def instrumenter() -> Generator[ExceptionInstrumenter, None, None]:
    Context.reset()
    instrumenter = ExceptionInstrumenter()
    instrumenter.setup()
    yield instrumenter
    instrumenter.teardown()


@pytest.mark.usefixtures("instrumenter")
def test_view_exception(live_server):
    url = live_server + "/view_exception/"
    resp = requests.get(url)
    assert resp.status_code == 500

    exc_namespace = "exc"

    Context.get("type", namespace=exc_namespace)
    assert Context.get("type", namespace=exc_namespace) == "MyError"
    assert Context.get("msg", namespace=exc_namespace) == "Oh noes!"

    assert re.match(r"app\.py:\d+:view_exception", Context.get("loc", namespace=exc_namespace))
    assert re.match(r"app\.py:\d+:func_that_throws", Context.get("cause_loc", namespace=exc_namespace))


# TODO: need to add template exception handling
