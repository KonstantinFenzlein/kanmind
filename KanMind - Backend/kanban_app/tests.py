from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from kanban_app.models import Boards, Comment, DashboardTasks


def make_user(username, email, first_name='', last_name='', password='testpass123'):  # Erstellt und speichert einen Django-User mit den angegebenen Daten.
    return User.objects.create_user(
        username=username, email=email, password=password,
        first_name=first_name, last_name=last_name,
    )


def auth(user):  # Gibt den Authorization-Header-String für den übergebenen User zurück.
    token, _ = Token.objects.get_or_create(user=user)
    return f'Token {token.key}'


def make_board(title, owner, members=None):  # Erstellt ein Board mit Owner als Mitglied und fügt optionale weitere Mitglieder hinzu.
    board = Boards.objects.create(title=title, owner=owner)
    board.members.add(owner)
    if members:
        board.members.add(*members)
    return board


def make_task(title, board, created_by, description='desc', status_val='to-do',  # Erstellt eine Task mit den angegebenen Feldern und optionalem Assignee/Reviewer.
              priority='medium', assignee=None, reviewer=None):
    return DashboardTasks.objects.create(
        title=title, description=description, board=board,
        created_by=created_by, status=status_val, priority=priority,
        assignee_id=assignee, reviewer_id=reviewer,
    )


class ModelStrTests(APITestCase):  # Testet die __str__-Methoden aller Kanban-Models.
    def setUp(self):  # Legt einen einfachen Testnutzer an.
        self.user = make_user('u', 'u@example.com')

    def test_board_str(self):  # Die __str__-Methode von Boards gibt den Board-Titel zurück.
        board = Boards.objects.create(title='MyBoard', owner=self.user)
        self.assertEqual(str(board), 'MyBoard')

    def test_dashboardtask_str(self):  # Die __str__-Methode von DashboardTasks gibt den Task-Titel zurück.
        board = Boards.objects.create(title='B', owner=self.user)
        task = DashboardTasks.objects.create(title='MyTask', description='D', board=board)
        self.assertEqual(str(task), 'MyTask')

    def test_comment_str(self):  # Die __str__-Methode von Comment gibt den Kommentarinhalt zurück.
        board = Boards.objects.create(title='B', owner=self.user)
        task = DashboardTasks.objects.create(title='T', description='D', board=board)
        comment = Comment.objects.create(task=task, content='Short comment', author=self.user)
        self.assertEqual(str(comment), 'Short comment')


class UserEmailListTests(APITestCase):  # Testet GET /api/email-check/.
    url = '/api/email-check/'

    def setUp(self):  # Legt einen anfragenden User und einen Zielnutzer an und authentifiziert den Client.
        self.user = make_user('owner', 'owner@example.com')
        self.target = make_user('target', 'target@example.com', 'Target', 'User')
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.user))

    def test_found_user_returns_200_with_data(self):  # Suche nach existierender E-Mail gibt 200 mit ID, Email und vollständigem Namen zurück.
        response = self.client.get(self.url, {'email': 'target@example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'target@example.com')
        self.assertEqual(response.data['fullname'], 'Target User')

    def test_user_not_found_returns_404(self):  # Suche nach nicht registrierter E-Mail gibt 404 zurück.
        response = self.client.get(self.url, {'email': 'nobody@example.com'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_missing_email_param_returns_400(self):  # Anfrage ohne Email-Parameter gibt 400 zurück.
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_email_format_returns_400(self):  # Ein ungültiges E-Mail-Format wird mit 400 abgelehnt.
        response = self.client.get(self.url, {'email': 'not-an-email'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_returns_401(self):  # Unauthentifizierte Anfrage an den Email-Check-Endpoint gibt 401 zurück.
        self.client.credentials()
        response = self.client.get(self.url, {'email': 'target@example.com'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BoardViewTests(APITestCase):  # Testet GET und POST /api/boards/.
    url = '/api/boards/'

    def setUp(self):  # Legt zwei unabhängige Nutzer an.
        self.owner = make_user('owner', 'owner@example.com')
        self.other = make_user('other', 'other@example.com')

    def test_list_returns_only_owned_boards(self):  # Board-Liste enthält nur Boards, bei denen der User Owner ist, nicht fremde Boards.
        make_board('Mine', self.owner)
        make_board('Theirs', self.other)
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Mine')

    def test_list_includes_boards_where_user_is_member(self):  # Board-Liste enthält auch Boards, bei denen der User Mitglied, aber nicht Owner ist.
        make_board('Shared', self.other, members=[self.owner])
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_response_contains_expected_fields(self):  # Die Board-Liste enthält alle erwarteten Kennzahl-Felder in der Antwort.
        make_board('Board', self.owner)
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.get(self.url)
        board_data = response.data[0]
        for field in ('id', 'title', 'member_count', 'ticket_count',
                      'tasks_to_do_count', 'tasks_high_prio_count', 'owner_id'):
            self.assertIn(field, board_data)

    def test_create_board_sets_owner_and_adds_as_member(self):  # Beim Erstellen eines Boards wird der eingeloggte User automatisch als Owner und Mitglied gesetzt.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.post(self.url, {'title': 'New', 'members': []}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        board = Boards.objects.get(title='New')
        self.assertEqual(board.owner, self.owner)
        self.assertIn(self.owner, board.members.all())

    def test_create_board_with_additional_member(self):  # Beim Erstellen eines Boards können weitere Mitglieder direkt hinzugefügt werden.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.post(
            self.url, {'title': 'Team', 'members': [self.other.id]}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        board = Boards.objects.get(title='Team')
        self.assertIn(self.other, board.members.all())

    def test_unauthenticated_list_returns_401(self):  # Unauthentifizierte GET-Anfrage auf die Board-Liste gibt 401 zurück.
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_create_returns_401(self):  # Unauthentifizierte POST-Anfrage zum Erstellen eines Boards gibt 401 zurück.
        response = self.client.post(self.url, {'title': 'X', 'members': []}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

