from typing import TYPE_CHECKING

from gunicorn import glogging
from gunicorn.http.message import Request
from gunicorn.http.wsgi import Response

if TYPE_CHECKING:
    from gunicorn_django_wide_events.monitors.arbiter import SaturationStats


class Logger(glogging.Logger):
    def access(self, resp: Response, req: Request, environ: dict, request_time: float):
        super().access(resp, req, environ, request_time)
        stats: SaturationStats = req.saturation_stats
        print(f"{stats.workers_total=}")
        print(f"{stats.workers_active=}")
        print(f"{stats.backlog=}")
