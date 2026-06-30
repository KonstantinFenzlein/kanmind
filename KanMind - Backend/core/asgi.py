# ASGI-Konfiguration für das core-Projekt.
#
# Stellt das ASGI-Callable als Modul-Variable mit dem Namen ``application`` bereit.
#
# Weitere Informationen zu dieser Datei findest du unter
# https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_asgi_application()
