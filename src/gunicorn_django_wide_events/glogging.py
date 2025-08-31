from multiprocessing.shared_memory import SharedMemory

from gunicorn import glogging
from gunicorn.http.message import Request
from gunicorn.http.wsgi import Response

from gunicorn_django_wide_events.monitors.arbiter import stats_struct


class Logger(glogging.Logger):
    def access(self, resp: Response, req: Request, environ: dict, request_time: float):
        super().access(resp, req, environ, request_time)
        arbiter_stats = SharedMemory(req._arbiter_stats_name)
        workers, backlog, _ = stats_struct.unpack(arbiter_stats.buf)
        print(f"{req._arbiter_stats_name=}")
        print(f"{workers=}")
        print(f"{backlog=}")
