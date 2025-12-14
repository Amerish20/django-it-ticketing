import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "it_ticketing.deployment" if "WEBSITE_HOSTNAME" in os.environ else "it_ticketing.settings"
)

application = get_wsgi_application()
