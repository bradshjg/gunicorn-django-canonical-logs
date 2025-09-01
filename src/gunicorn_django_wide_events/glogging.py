import datetime

from gunicorn import glogging
from gunicorn.http.wsgi import Response

from gunicorn_django_wide_events.event_context import context


class Logger(glogging.Logger):
    def access(self, resp: Response, _, environ: dict, request_time: datetime.timedelta):
        access_context = {
            "req": {
                "method": environ.get("REQUEST_METHOD"),
                "path": environ.get("PATH_INFO"),
                "referrer": environ.get("HTTP_REFERER"),
                "user_agent": environ.get("HTTP_USER_AGENT"),
            },
            "resp": {"status": resp.status_code, "time": f"{request_time.total_seconds():.3f}"},
        }

        context.update(access_context)
        self.access_log.info(str(context))
