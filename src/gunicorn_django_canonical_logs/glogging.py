from gunicorn import glogging
from gunicorn.http.message import Request

from gunicorn_django_canonical_logs.event_context import Context
from gunicorn_django_canonical_logs.instrumenters.registry import instrumenter_registry
from gunicorn_django_canonical_logs.logfmt import LogFmt


class Logger(glogging.Logger):
    EVENT_TYPE = "type"
    EVENT_NAMESPACE = "event"

    def access(self, _resp, req: Request, *_args, **_kwargs):
        # gunicorn calls this on abort, but the data is weird (e.g. request timing is abort handler timing?); silence it
        if req.timed_out:
            return

        self._emit_log("request")

    def timeout(self):
        self._emit_log("timeout")

    def _emit_log(self, event_type: str) -> None:
        Context.update(context={self.EVENT_TYPE: event_type}, namespace=self.EVENT_NAMESPACE, beginning=True)

        for instrumenter in instrumenter_registry.values():
            instrumenter.call()

        self.access_log.info(LogFmt.format(Context))
