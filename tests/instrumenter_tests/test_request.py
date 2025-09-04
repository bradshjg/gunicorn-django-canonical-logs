import re

from gunicorn_django_wide_events.event_context import context
from gunicorn_django_wide_events.instrumenters.request import RequestInstrumenter


def test_request(client, settings):
    settings.MIDDLEWARE = [RequestInstrumenter().request_middleware_string_path]
    resp = client.get("/ok/")
    assert resp.status_code == 200

    req_context = context["req"]
    expected_req_context = {
        "method": "GET",
        "path": "/ok/",
        "view": "app.ok",
        "referrer": None,
        "user_agent": None
    }

    assert req_context == expected_req_context

    resp_context = context["resp"]
    assert resp_context["status"] == 200

    assert re.match(r"0\.\d{3}", resp_context["time"])
    assert re.match(r"0\.\d{3}", resp_context["cpu_time"])


# TODO test this under failure conditions as well, thinking like not found, other Django stuff
