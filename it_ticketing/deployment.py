import os
from urllib.parse import urlparse

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
