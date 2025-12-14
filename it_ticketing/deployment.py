import os
from .settings import *

ALLOWED_HOSTS = [os.environ.get("WEBSITE_HOSTNAME")]
CSRF_TRUSTED_ORIGINS = [f"https://{os.environ.get('WEBSITE_HOSTNAME')}"]
DEBUG = False
# ---------------------------------------
# Database (Azure PostgreSQL Flexible Server)
# ---------------------------------------

# Example format:
# dbname=wataniyaticket-database host=wataniyaticket-server.postgres.database.azure.com
# user=yehtkhqifw password=Z2TvqpRz2xNZ$n23 sslmode=require

conn_str = os.environ["AZURE_POSTGRESQL_CONNECTIONSTRING"]

parts = conn_str.split(" ")
params = dict(p.split("=") for p in parts if "=" in p)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": params["dbname"],
        "USER": params["user"],
        "PASSWORD": params["password"],
        "HOST": params["host"],
        "PORT": params.get("port", "5432"),
        "OPTIONS": {
            "sslmode": "require",
        },
    }
}

# -------------------------------------------------
# STATIC files on Azure using WhiteNoise
# -------------------------------------------------
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"
