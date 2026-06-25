# WSGI-Konfiguration für das core-Projekt.
#
# Stellt das WSGI-Callable als Modul-Variable mit dem Namen ``application`` bereit.
#
# Weitere Informationen zu dieser Datei findest du unter
# https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_wsgi_application()
