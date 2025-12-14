"""
WSGI config for it_ticketing project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

# If running on Azure (WEBSITE_HOSTNAME exists), use deployment settings
if 'WEBSITE_HOSTNAME' in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'it_ticketing.deployment')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'it_ticketing.settings')

application = get_wsgi_application()

