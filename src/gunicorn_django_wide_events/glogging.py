import datetime

from gunicorn import glogging
from gunicorn.http.message import Request
from gunicorn.http.wsgi import Response

from gunicorn_django_wide_events.event_context import context  # FIXME: should import as `from gdwe import context`
from gunicorn_django_wide_events.instrumenters.instrumenters import (
    instrumenter_registry,  # FIXME: should import as `from gdwe.instrumenters import instrumener_registry`
)


class Logger(glogging.Logger):
    def access(self, resp: Response, req: Request, environ: dict, request_time: datetime.timedelta):
        # TODO: access logs also fire on the unhandled exceptions due to timeouts. Fair.
        # If the worker is able to gracefully exit we'll get both, acceptable?
        context["type"] = "request"
        access_context = {
            "req": {
                "method": environ.get("REQUEST_METHOD"),
                "path": environ.get("PATH_INFO"),
                "referrer": environ.get("HTTP_REFERER"),
                "user_agent": environ.get("HTTP_USER_AGENT"),
                "timed_out": getattr(req, "timed_out", False),
            },
            "resp": {"status": getattr(resp, "status_code", None), "time": f"{request_time.total_seconds():.3f}"},
        }
        context.update(access_context)

        for instrumenter in instrumenter_registry.values():
            instrumenter.call()

        self.access_log.info(str(context))

    def timeout(
        self, req: Request, request_time: int
    ):  # FIXME: this isn't an int necessarily (that's true all the way down)
        context["type"] = "timeout"
        # FIXME: centralize req context, should happen earlier!
        req_context = {
            "method": req.method,
            "path": req.path,
        }
        context["req"] = req_context
        context["resp"] = {"time": request_time}

        for instrumenter in instrumenter_registry.values():
            instrumenter.call()

        self.access_log.info(str(context))
