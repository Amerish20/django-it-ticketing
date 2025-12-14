#!/usr/bin/env python
import os
import sys

def main():
    os.environ.setdefault(
        'DJANGO_SETTINGS_MODULE',
        'it_ticketing.deployment' if 'WEBSITE_HOSTNAME' in os.environ else 'it_ticketing.settings'
    )
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
