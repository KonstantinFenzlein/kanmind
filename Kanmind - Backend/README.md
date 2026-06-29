# Kanban Board API

## Überblick
Die Kanban Board API ist ein **Django-REST-Framework-Projekt** zur Verwaltung von Boards, Aufgaben und Kommentaren mit rollenbasierten Berechtigungen.  
Sie nutzt **Token-Authentifizierung** für sicheren Zugriff und unterstützt eine durchsuchbare API für Entwicklung und Tests.

## Features
- Benutzerregistrierung sowie An- und Abmeldung
- CRUD-Operationen für **Boards** und **Tasks**
- Beim Erstellen eines Boards wird der authentifizierte Benutzer als Eigentümer gespeichert und automatisch als Mitglied hinzugefügt
- Kommentarfunktion für Tasks
- Berechtigungen auf Objektebene:
  - Nur Verfasser können ihre Kommentare bearbeiten
  - Nur Admins oder Verfasser können Kommentare löschen
- Token-basierte Authentifizierung
- Browsbare API für die Entwicklung

# Installation
## Befolgen Sie diese Schritte, um das Projekt lokal einzurichten:

## 1. Repository clonen
  git clone https://github.com/KonstantinFenzlein/kanmind.git <br>
  cd kanmind/"Kanmind - Backend"/project.KanMind-backend

## 2. Virtuelle Umgebung einrichten
  python -m venv env

## 3. Virtuelle Umgebung aktivieren
  source env/bin/activate  # <b>Linux/Mac</b>  <br>
  env\Scripts\activate     # <b>Windows</b> 

## 4. Python-Abhängigkeiten installieren
  pip install -r requirements.txt

## 5. Datenbank-Migrationen erstellen
python manage.py makemigrations

## 6. Datenbankmigrationen anwenden
  python manage.py migrate

## 7. Superuser (admin account) anlegen
  python manage.py createsuperuser

## 8. Starten Sie den Entwicklungsserver
  python manage.py runserver  <br>
  The project will be running at http://127.0.0.1:8000/

# Tests ausführen
  python manage.py test <br>
  pytest  <br>
  coverage run manage.py test && coverage report

# API-Endpunkte

## Authentifizierung (`auth_app`)
| Methode | Endpunkt              | Beschreibung           |
|---------|------------------------|-------------------------|
| POST    | `/api/registration/`  | Benutzer registrieren  |
| POST    | `/api/login/`         | Anmelden, liefert Token |
| POST    | `/api/logout/`        | Abmelden               |

## Boards & Tasks (`kanban_app`)
| Methode             | Endpunkt                                   | Beschreibung                          |
|---------------------|---------------------------------------------|----------------------------------------|
| GET                 | `/api/email-check/`                        | Prüft, ob eine E-Mail registriert ist |
| GET, POST           | `/api/boards/`                             | Boards auflisten / erstellen          |
| GET, PUT/PATCH, DELETE | `/api/boards/<board_id>/`               | Einzelnes Board abrufen/ändern/löschen |
| POST                | `/api/tasks/`                              | Task erstellen                        |
| GET                 | `/api/tasks/assigned-to-me/`               | Mir zugewiesene Tasks                 |
| GET                 | `/api/tasks/reviewing/`                    | Tasks, bei denen ich Reviewer bin     |
| GET, PUT/PATCH, DELETE | `/api/tasks/<task_id>/`                 | Einzelne Task abrufen/ändern/löschen  |
| GET, POST           | `/api/tasks/<task_pk>/comments/`           | Kommentare einer Task auflisten/erstellen |
| GET, PUT/PATCH, DELETE | `/api/tasks/<task_pk>/comments/<pk>/`   | Einzelnen Kommentar abrufen/ändern/löschen |

Alle Endpunkte (außer Registrierung/Login) erfordern Token-Authentifizierung über den Header `Authorization: Token <dein-token>`.

# Projectstruktur
## core/
├── settings.py      # Projekteinstellungen <br>
├── urls.py          # Root-URL-Konfiguration <br>
├── asgi.py  <br>
├── wsgi.py

## kanban_app/
├── models.py        # Boards, Tasks, Comments <br>
├── admin.py  <br>
└── api/  <br>
├── views.py         # API views  <br>
├── serializer.py    # DRF serializers  <br>
└── urls.py

## auth_app/
├── models.py  <br>
├── admin.py  <br>
└── api/  <br>
├── views.py         # Registration, login, logout  <br>
├── serializers.py   # DRF serializers  <br>
├── urls.py  <br>
└── permissions.py   # Custom permissions

manage.py
requirements.txt
README.md
