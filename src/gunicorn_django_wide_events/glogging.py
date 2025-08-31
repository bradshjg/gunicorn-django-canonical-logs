import logging

from gunicorn import glogging
from gunicorn.http.message import Request
from gunicorn.http.wsgi import Response

logger = logging.getLogger("request")
logger.propagate = False

class Logger(glogging.Logger):
    def access(self, resp: Response, req: Request, environ: dict, request_time: float):
        super().access(resp, req, environ, request_time)
        logger.info("howdy")
