import datetime

from gunicorn import glogging
from gunicorn.http.message import Request
from gunicorn.http.wsgi import Response

from gunicorn_django_wide_events.event_context import context  # FIXME: should import as `from gdwe import context`
from gunicorn_django_wide_events.instrumenters.instrumenters import (
    instrumenter_registry,  # FIXME: should import as `from gdwe.instrumenters import instrumener_registry`
)

# TODO: consider if we want to also support relatively minimal event logging that doesn't assume fancy log setup but can be emitted within a request?
# If so, maybe use the request subset of context at least?
class Logger(glogging.Logger):
    def access(self, _resp, req, *args, **kwargs):
        # gunicorn calls this on abort, but the data is weird (e.g. request timing is abort handler timing?); silence it
        if req.timed_out:
            return

        context["type"] = "request"

        for instrumenter in instrumenter_registry.values():
            instrumenter.call()

        self.access_log.info(str(context))

    def timeout(self):
        context["type"] = "timeout"

        for instrumenter in instrumenter_registry.values():
            instrumenter.call()

        self.access_log.info(str(context))
