from django.conf import settings
from django.core.management import execute_from_command_line
from django.core.wsgi import get_wsgi_application
from django.http import HttpResponse
from django.urls import path

settings.configure(
    ROOT_URLCONF=__name__,
    DEBUG=True,
    SECRET_KEY="not-so-secret",
)


def hello(_):
    return HttpResponse("Hello!")


def howdy(_):
    return HttpResponse("Howdy!")


urlpatterns = [path("hello/", hello), path("howdy/", howdy)]

application = get_wsgi_application()

if __name__ == "__main__":
    execute_from_command_line()
