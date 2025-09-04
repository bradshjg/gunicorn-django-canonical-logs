import time

from django.conf import settings

from gunicorn_django_wide_events.instrumenters.base import BaseInstrumenter
from gunicorn_django_wide_events.instrumenters.instrumenters import register_instrumenter
from gunicorn_django_wide_events.event_context import context


def _DjangoMiddleware(get_response):
# One-time configuration and initialization.

    def context_middleware(request):

        start_time = time.monotonic()
        start_cpu_time = time.process_time()

        response = get_response(request)

        request_context = {
            "req": {
                "method": request.method,
                "path": request.path,
                "view": getattr(request.resolver_match, "view_name", None),
                "referrer": request.headers.get("referrer"),
                "user_agent": request.headers.get("user-agent"),
            },
            "resp": {
                "time": f"{time.monotonic() - start_time:.3f}",
                "cpu_time": f"{time.process_time() - start_cpu_time:.3f}",
                "status": response.status_code,
            },
        }

        context.update(request_context)

        return response

    return context_middleware


@register_instrumenter
class RequestInstrumenter(BaseInstrumenter):
    def __init__(self):
        self.middleware_setting = "MIDDLEWARE"
        self.request_middleware_string_path = '.'.join([self.__module__, _DjangoMiddleware.__qualname__])

    def setup(self):
        settings_middleware = getattr(settings, self.middleware_setting)

        settings_middleware = list(settings_middleware) # ensure access to insert method
        settings_middleware.insert(0, self.request_middleware_string_path)

        setattr(settings, self.middleware_setting, settings_middleware)

    def teardown(self):
        settings_middleware = getattr(settings, self.middleware_setting)
        settings_middleware.remove(self.request_middleware_string_path)
