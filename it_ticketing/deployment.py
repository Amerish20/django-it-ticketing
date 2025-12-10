import os
from .settings import *

DEBUG = False

ALLOWED_HOSTS = [os.environ["WEBSITE_HOSTNAME"]]
CSRF_TRUSTED_ORIGINS = [f'https://{os.environ["WEBSITE_HOSTNAME"]}']

# Azure PostgreSQL Connection String
conn_str = os.environ["AZURE_POSTGRESQL_CONNECTIONSTRING"]

# Azure gives: host=xxx dbname=xxx user=xxx password=xxx port=5432
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
    }
}

# Static files for Azure
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
