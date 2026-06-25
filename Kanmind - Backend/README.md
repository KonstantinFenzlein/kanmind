# Kanban Board API

## Überblick
Die Kanban Board API ist ein **Django-REST-Framework-Projekt** zur Verwaltung von Boards, Aufgaben und Kommentaren mit rollenbasierten Berechtigungen.  
Sie nutzt **Token-Authentifizierung** für sicheren Zugriff und unterstützt eine durchsuchbare API für Entwicklung und Tests.

---

## Email-Check-Endpunkt
Prüft, ob eine E-Mail-Adresse zu einem registrierten Benutzer gehört und gibt den Benutzer zurück, falls vorhanden.

### Query-Parameter
- `email`: Die zu prüfende E-Mail-Adresse.

### Erfolgantwort
```json
{
  "id": 1,
  "email": "max.mustermann@example.com",
  "fullname": "Max Mustermann"
}
```

### Berechtigungen
- `401`: Nicht autorisiert. Der Benutzer muss eingeloggt sein.
- `400`: Ungültige Anfrage. Die E-Mail-Adresse fehlt oder hat ein falsches Format.
- `404`: E-Mail nicht gefunden.

---

## Zugewiesene Tasks-Endpunkt
Ruft alle Tasks ab, die dem aktuell authentifizierten Benutzer als Bearbeiter zugewiesen sind.

### URL
- `tasks/assigned-to-me/`

### Erfolgantwort
Gibt eine Liste der zugewiesenen Tasks zurück.

### Berechtigungen
- `401`: Nicht autorisiert. Der Benutzer muss eingeloggt sein.

---

## Reviewer-Tasks-Endpunkt
Ruft alle Tasks ab, bei denen der aktuell authentifizierte Benutzer als Prüfer eingetragen ist.

### URL
- `tasks/reviewing/`

### Erfolgantwort
Gibt eine Liste der Tasks zurück, die dem Benutzer zur Überprüfung zugewiesen sind.

### Berechtigungen
- `401`: Nicht autorisiert. Der Benutzer muss eingeloggt sein.

---

## Task-Erstell-Endpunkt
Erstellt eine neue Task innerhalb eines Boards.

### URL
- `tasks/`

### Request Body
```json
{
  "board": 12,
  "title": "Code-Review durchführen",
  "description": "Den neuen PR für das Feature X überprüfen",
  "status": "review",
  "priority": "medium",
  "assignee_id": 13,
  "reviewer_id": 1,
  "due_date": "2025-02-27"
}
```

### Erfolgantwort
Die Antwort enthält die erstellte Task mit allen zugehörigen Informationen.

### Berechtigungen
- `401`: Nicht autorisiert. Der Benutzer muss eingeloggt sein.
- `403`: Verboten. Der Benutzer muss Mitglied des Boards sein.
- `404`: Board nicht gefunden.

### Hinweise
- Zulässige Statuswerte: `to-do`, `in-progress`, `review`, `done`
- Zulässige Prioritätswerte: `low`, `medium`, `high`
- `assignee_id` und `reviewer_id` dürfen leer bleiben, müssen aber, wenn gesetzt, Mitglieder des Boards sein.

---

## Task-Update-Endpunkt
Aktualisiert eine bestehende Task. Nur Mitglieder des Boards, zu dem die Task gehört, können sie bearbeiten.

### URL-Parameter
- `task_id`: Die ID der zu aktualisierenden Task.

### Request Body
```json
{
  "title": "Code-Review abschließen",
  "description": "Den PR fertig prüfen und Feedback geben",
  "status": "done",
  "priority": "high",
  "assignee_id": 13,
  "reviewer_id": 1,
  "due_date": "2025-02-28"
}
```

### Erfolgantwort
Die Antwort enthält die aktualisierte Task mit allen geänderten Werten.

### Berechtigungen
- `401`: Nicht autorisiert. Der Benutzer muss eingeloggt sein.
- `403`: Verboten. Der Benutzer muss Mitglied des Boards sein, zu dem die Task gehört.
- `404`: Task nicht gefunden.

### Hinweise
- Das Ändern der Board-ID ist nicht erlaubt.
- `assignee_id` und `reviewer_id` müssen, wenn gesetzt, Mitglieder des Boards sein.

---

## Task-Lösch-Endpunkt
Löscht eine bestehende Task. Nur der Ersteller der Task oder der Eigentümer des Boards kann die Task löschen.

### URL-Parameter
- `task_id`: Die ID der zu löschenden Task.

### Erfolgantwort
Bei erfolgreichem Löschen wird keine Antwortinhalte zurückgegeben.

### Berechtigungen
- `401`: Nicht autorisiert. Der Benutzer muss eingeloggt sein.
- `403`: Verboten. Nur der Ersteller der Task oder der Board-Eigentümer kann die Task löschen.
- `404`: Task nicht gefunden.

### Hinweise
- Die Löschung ist dauerhaft und entfernt die Task unwiderruflich.
- Die Board-ID kann nicht geändert werden.

---

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

---

## Board-Detail-Endpunkt
Ruft die Informationen eines bestimmten Boards zusammen mit den zugehörigen Tasks ab und erlaubt das Aktualisieren von Titel und Mitgliedern.

### URL-Parameter
- `board_id`: Die ID des Boards, dessen Informationen und zugewiesene Tasks abgerufen werden sollen.

### Update-Anfrage
Der PATCH-Endpoint aktualisiert den Boardtitel und die Mitglieder. Mitglieder, die nicht mehr in der Liste stehen, werden entfernt. Tasks werden über diesen Endpoint nicht geändert.

```json
{
  "title": "Changed title",
  "members": [1, 54]
}
```

### Erfolgantwort
Die Antwort enthält die Board-Informationen, die Mitglieder und die zugehörigen Tasks. Im Projekt enthält jedes Task-Objekt zusätzlich das Feld `board`, während `assignee_id` und `reviewer_id` nur zum Schreiben verwendet werden.

Beim PATCH-Update enthält die Antwort das aktualisierte Board mit `owner_data` und `members_data`.

```json
{
  "id": 1,
  "title": "Projekt X",
  "owner_id": 12,
  "members": [
    {
      "id": 1,
      "email": "max.mustermann@example.com",
      "fullname": "Max Mustermann"
    },
    {
      "id": 54,
      "email": "max.musterfrau@example.com",
      "fullname": "Maxi Musterfrau"
    }
  ],
  "tasks": [
    {
      "id": 5,
      "board": 1,
      "title": "API-Dokumentation schreiben",
      "description": "Die API-Dokumentation für das Backend vervollständigen",
      "status": "to-do",
      "priority": "high",
      "assignee": null,
      "reviewer": {
        "id": 1,
        "email": "max.mustermann@example.com",
        "fullname": "Max Mustermann"
      },
      "due_date": "2025-02-25",
      "comments_count": 0
    },
    {
      "id": 8,
      "board": 1,
      "title": "Code-Review durchführen",
      "description": "Den neuen PR für das Feature X überprüfen",
      "status": "review",
      "priority": "medium",
      "assignee": {
        "id": 1,
        "email": "max.mustermann@example.com",
        "fullname": "Max Mustermann"
      },
      "reviewer": null,
      "due_date": "2025-02-27",
      "comments_count": 0
    }
  ]
}
```

---

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


# Projectstruktur
## kanban_app/
├── models.py        # Boards, Tasks, Comments <br>
├── views.py         # API views  <br>
├── serializers.py   # DRF serializers  <br>
├── urls.py

## auth_app/
├── views.py         # Registration, login, logout  <br>
├── serializers.py   # DRF serializers  <br>
├── urls.py  <br>
├── permissions.py   # Custom permissions

manage.py
requirements.txt
README.md
