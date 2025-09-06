from typing import Generator

import pytest
import requests

from gunicorn_django_wide_events.event_context import Context
from gunicorn_django_wide_events.instrumenters.database import DatabaseInstrumenter


@pytest.fixture
def instrumenter() -> Generator[DatabaseInstrumenter, None, None]:
    Context.reset()
    instrumenter = DatabaseInstrumenter()
    instrumenter.setup()
    yield instrumenter
    instrumenter.teardown()


def test_queries(instrumenter, live_server):
    url = live_server + "/db_queries/"
    resp = requests.get(url)
    assert resp.status_code == 200

    db_namespace = "db"

    instrumenter.call()

    assert Context.get("queries", namespace=db_namespace) == 2
    assert Context.get("time", namespace=db_namespace) is not None


def test_reset(instrumenter, live_server):
    url = live_server + "/db_queries/"
    resp = requests.get(url)
    assert resp.status_code == 200

    db_namespace = "db"

    instrumenter.call()

    assert Context.get("queries", namespace=db_namespace) == 2
    assert Context.get("time", namespace=db_namespace) is not None

    instrumenter.call()

    assert Context.get("queries", namespace=db_namespace) == 0
    assert Context.get("time", namespace=db_namespace) == 0
