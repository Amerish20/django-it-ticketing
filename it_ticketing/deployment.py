import os
from urllib.parse import urlparse
from .settings import *

ROOT_URLCONF = "it_ticketing.urls"

DEBUG = True  # keep ON for now

ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = ["https://*.azurewebsites.net"]

SECRET_KEY = os.environ["SECRET_KEY"]

DATABASES = {}

conn_str = os.environ.get("AZURE_POSTGRESQL_CONNECTIONSTRING")

if conn_str.startswith("postgres"):
    # URL style (recommended)
    url = urlparse(conn_str)

    DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": url.path[1:],   # removes leading /
        "USER": url.username,
        "PASSWORD": url.password,
        "HOST": url.hostname,
        "PORT": url.port or "5432",
        "OPTIONS": {"sslmode": "require"},
    }
else:
    # key=value style
    params = dict(
        item.split("=", 1)
        for item in conn_str.split()
    )

    DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": params["dbname"],
        "USER": params["user"],
        "PASSWORD": params["password"],
        "HOST": params["host"],
        "PORT": "5432",
        "OPTIONS": {"sslmode": "require"},
    }

# ---------------------------------------
# Static files
# ---------------------------------------
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"