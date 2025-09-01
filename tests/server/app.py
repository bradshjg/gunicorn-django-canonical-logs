from pathlib import Path

from django.conf import settings
from django.core.management import execute_from_command_line
from django.core.wsgi import get_wsgi_application
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import path

from gunicorn_django_wide_events.event_context import context


class MyError(Exception):
    def __init__(self):
        super().__init__("Oh noes!")


def func_that_throws():
    raise MyError


def ok(_):
    return HttpResponse("OK!")


def view_exception(_):
    func_that_throws()
    return HttpResponse("We shouldn't get here!")


def template_syntax_exception(request):
    return render(request, "syntax_exception.html")


def template_callable_exception(request):
    return render(request, "callable_exception.html", {"callable": func_that_throws})


def custom_event(_):
    context["custom_event"] = 1
    return HttpResponse("Added custom event!")


urlpatterns = [
    path("ok/", ok),
    path("view_exception/", view_exception),
    path("template_syntax_exception/", template_syntax_exception),
    path("template_callable_exception/", template_callable_exception),
    path("named_ok/", ok, name="named_ok_view"),
    path("custom_event/", custom_event),
]

application = get_wsgi_application()

if __name__ == "__main__":
    execute_from_command_line()
