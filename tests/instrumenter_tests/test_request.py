import re

from gunicorn_django_wide_events import Context
from gunicorn_django_wide_events.instrumenters.request import RequestInstrumenter


def test_request(client, settings):
    settings.MIDDLEWARE = [RequestInstrumenter().request_middleware_string_path]
    resp = client.get("/ok/")
    assert resp.status_code == 200

    expected_req_context = {"method": "GET", "path": "/ok/", "view": "app.ok", "referrer": None, "user_agent": None}

    req_namespace = "req"
    resp_namespace = "resp"

    for key, val in expected_req_context.items():
        assert Context.get(key, namespace=req_namespace) == val

    assert Context.get("status", namespace=resp_namespace) == 200

    assert re.match(r"0\.\d{3}", Context.get("time", namespace=resp_namespace))
    assert re.match(r"0\.\d{3}", Context.get("cpu_time", namespace=resp_namespace))


# TODO: test this under failure conditions as well, thinking like not found, other Django stuff
