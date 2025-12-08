import os
from .settings import *
from .settings import BASE_DIR
import dj_database_url

# ========================
# Secret Key
# ========================
SECRET_KEY = os.environ.get('SECRET', SECRET_KEY)  # fallback to settings.py

# ========================
# Allowed Hosts
# ========================
WEBSITE_HOSTNAME = os.environ.get('WEBSITE_HOSTNAME')
if WEBSITE_HOSTNAME:
    ALLOWED_HOSTS = [WEBSITE_HOSTNAME]
    CSRF_TRUSTED_ORIGINS = [f"https://{WEBSITE_HOSTNAME}"]

DEBUG = False

# ========================
# Static Files (WhiteNoise)
# ========================
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# ========================
# Database
# ========================
conn_str = os.environ.get("AZURE_POSTGRESQL_CONNECTIONSTRING")

if conn_str:
    DATABASES = {
        'default': dj_database_url.parse(
            conn_str,
            conn_max_age=600,
            ssl_require=True
        )
    }
