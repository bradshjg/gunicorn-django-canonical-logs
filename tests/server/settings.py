from pathlib import Path

ROOT_URLCONF = "app"

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

SECRET_KEY = "not-so-secret"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [Path(__file__).parent / "templates"],
    }
]

STATIC_URL = "static/"  # HACK otherwise Django liveserver test cases parse the base url as bytes
