from pathlib import Path

from django.conf import settings
from django.core.management import execute_from_command_line
from django.core.wsgi import get_wsgi_application
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import path

settings.configure(
    ROOT_URLCONF=__name__,
    DEBUG=True,
    SECRET_KEY="not-so-secret",
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [Path(__file__).parent / "templates"],
        }
    ],
)


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


urlpatterns = [
    path("ok/", ok),
    path("view_exception/", view_exception),
    path("template_syntax_exception/", template_syntax_exception),
    path("template_callable_exception/", template_callable_exception),
    path("named_ok/", ok, name="named_ok_view"),
]

application = get_wsgi_application()

if __name__ == "__main__":
    execute_from_command_line()
