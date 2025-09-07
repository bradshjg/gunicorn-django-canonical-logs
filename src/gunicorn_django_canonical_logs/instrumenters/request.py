import time

from django.conf import settings

from gunicorn_django_canonical_logs.event_context import Context
from gunicorn_django_canonical_logs.instrumenters.base import BaseInstrumenter
from gunicorn_django_canonical_logs.instrumenters.registry import register_instrumenter


def _django_middleware(get_response):
    # One-time configuration and initialization.

    def context_middleware(request):
        start_time = time.monotonic()
        start_cpu_time = time.process_time()

        request_context = {
            "method": request.method,
            "path": request.path,
            "referrer": request.headers.get("referrer"),
            "user_agent": request.headers.get("user-agent"),
        }
        Context.update(namespace="req", context=request_context)

        response = get_response(request)

        response_context = {
            "view": getattr(request.resolver_match, "view_name", None),
            "time": f"{time.monotonic() - start_time:.3f}",
            "cpu_time": f"{time.process_time() - start_cpu_time:.3f}",
            "status": response.status_code,
        }
        Context.update(namespace="resp", context=response_context)

        return response

    return context_middleware


@register_instrumenter
class RequestInstrumenter(BaseInstrumenter):
    def __init__(self):
        self.middleware_setting = "MIDDLEWARE"
        self.request_middleware_string_path = f"{self.__module__}.{_django_middleware.__qualname__}"

    def setup(self):
        settings_middleware = getattr(settings, self.middleware_setting)

        settings_middleware = list(settings_middleware)  # ensure access to insert method
        settings_middleware.insert(0, self.request_middleware_string_path)

        setattr(settings, self.middleware_setting, settings_middleware)

    def teardown(self):
        settings_middleware: list = getattr(settings, self.middleware_setting)
        settings_middleware.remove(self.request_middleware_string_path)
