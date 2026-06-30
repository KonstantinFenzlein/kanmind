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


class BoardSingleViewTests(APITestCase):  # Testet GET, PATCH, PUT und DELETE /api/boards/<id>/.
    def setUp(self):  # Legt Owner, Mitglied, Außenseiter und ein Testboard an.
        self.owner = make_user('owner', 'owner@example.com')
        self.member = make_user('member', 'member@example.com')
        self.outsider = make_user('outsider', 'outsider@example.com')
        self.board = make_board('Board', self.owner, members=[self.member])
        self.url = f'/api/boards/{self.board.id}/'

    def test_owner_can_get_board_detail(self):  # Der Owner erhält die Board-Detailansicht inklusive Tasks-Liste mit 200.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Board')
        self.assertIn('tasks', response.data)

    def test_member_can_get_board_detail(self):  # Ein Mitglied kann die Board-Detailansicht mit 200 abrufen.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.member))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_outsider_get_returns_403(self):  # Ein Nicht-Mitglied erhält beim Abrufen des Boards 403.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.outsider))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_patch_title(self):  # Der Owner kann den Board-Titel per PATCH aktualisieren.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.patch(
            self.url, {'title': 'Updated', 'members': [self.owner.id, self.member.id]}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.board.refresh_from_db()
        self.assertEqual(self.board.title, 'Updated')

    def test_patch_with_members_field_maps_to_members_ids(self):  # Das Feld 'members' im PATCH-Body wird intern korrekt auf 'members_ids' gemappt.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.patch(
            self.url, {'title': 'X', 'members': [self.owner.id]}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_request_uses_all_fields(self):  # Ein PUT-Request auf ein Board läuft ohne Serverfehler durch.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.put(
            self.url,
            {'title': 'PutTitle', 'members': [self.owner.id, self.member.id]},
            format='json',
        )
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST))

    def test_owner_can_delete_board(self):  # Der Owner kann ein Board löschen, woraufhin es nicht mehr existiert.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Boards.objects.filter(id=self.board.id).exists())

    def test_delete_cascades_tasks_and_comments(self):  # Beim Löschen eines Boards werden zugehörige Tasks und deren Kommentare ebenfalls entfernt.
        task = make_task('T', self.board, self.owner)
        Comment.objects.create(task=task, content='Cmt', author=self.owner)
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        self.client.delete(self.url)
        self.assertFalse(DashboardTasks.objects.filter(id=task.id).exists())
        self.assertFalse(Comment.objects.filter(task=task).exists())

    def test_member_delete_returns_403(self):  # Ein einfaches Mitglied kann das Board nicht löschen und erhält 403.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.member))
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nonexistent_board_returns_404(self):  # Anfrage auf eine nicht existierende Board-ID gibt 404 zurück.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.get('/api/boards/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_get_returns_401(self):  # Unauthentifizierte Anfrage auf ein einzelnes Board gibt 401 zurück.
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_board_detail_ticket_and_task_counts(self):  # Die Board-Listenansicht zählt Tickets, To-do-Tasks, High-Priority-Tasks und Mitglieder korrekt.
        make_task('T1', self.board, self.owner, status_val='to-do', priority='high')
        make_task('T2', self.board, self.owner, status_val='done', priority='low')
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.get('/api/boards/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        board_data = response.data[0]
        self.assertEqual(board_data['ticket_count'], 2)
        self.assertEqual(board_data['tasks_to_do_count'], 1)
        self.assertEqual(board_data['tasks_high_prio_count'], 1)
        self.assertEqual(board_data['member_count'], 2)


class TaskViewTests(APITestCase):  # Testet POST /api/tasks/.
    url = '/api/tasks/'

    def setUp(self):  # Legt Owner, Mitglied, Außenseiter und ein Testboard an.
        self.owner = make_user('owner', 'owner@example.com')
        self.member = make_user('member', 'member@example.com')
        self.outsider = make_user('outsider', 'outsider@example.com')
        self.board = make_board('Board', self.owner, members=[self.member])

    def _task_data(self, **kwargs):  # Hilfsmethode: liefert Standard-Task-Daten mit optionalen Überschreibungen.
        return {
            'title': 'Task',
            'description': 'Desc',
            'board': self.board.id,
            'status': 'to-do',
            'priority': 'medium',
            **kwargs,
        }

    def test_owner_can_create_task(self):  # Der Board-Owner kann eine neue Task erstellen und erhält 201 mit den Task-Daten.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.post(self.url, self._task_data(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Task')

    def test_member_can_create_task(self):  # Ein Board-Mitglied kann ebenfalls eine Task erstellen.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.member))
        response = self.client.post(self.url, self._task_data(title='ByMember'), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_outsider_create_returns_403(self):  # Ein Nicht-Mitglied kann keine Task erstellen und erhält 403.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.outsider))
        response = self.client.post(self.url, self._task_data(), format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nonexistent_board_returns_404(self):  # Eine Task-Erstellung mit einer nicht existierenden Board-ID gibt 404 zurück.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.post(self.url, self._task_data(board=99999), format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_assignee_not_board_member_returns_400(self):  # Ein Assignee, der kein Board-Mitglied ist, wird mit 400 abgelehnt.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.post(
            self.url, self._task_data(assignee_id=self.outsider.id), format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reviewer_not_board_member_returns_400(self):  # Ein Reviewer, der kein Board-Mitglied ist, wird mit 400 abgelehnt.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.post(
            self.url, self._task_data(reviewer_id=self.outsider.id), format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_assignee_and_reviewer_returns_201(self):  # Eine Task mit gültigem Assignee und Reviewer (beide Mitglieder) wird erfolgreich erstellt.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.post(
            self.url,
            self._task_data(assignee_id=self.member.id, reviewer_id=self.owner.id),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('comments_count', response.data)

    def test_unauthenticated_create_returns_401(self):  # Unauthentifizierte Task-Erstellung gibt 401 zurück.
        response = self.client.post(self.url, self._task_data(), format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_board_field_returns_404(self):  # Eine Anfrage ohne Board-Feld gibt 404 zurück, da board=None kein Objekt findet.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.post(self.url, {'title': 'No board', 'description': 'X'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TasksSingleViewTests(APITestCase):  # Testet GET, PATCH und DELETE /api/tasks/<id>/.
    def setUp(self):  # Legt Owner, Mitglied, Außenseiter, Board und eine Testtask an.
        self.owner = make_user('owner', 'owner@example.com')
        self.member = make_user('member', 'member@example.com')
        self.outsider = make_user('outsider', 'outsider@example.com')
        self.board = make_board('Board', self.owner, members=[self.member])
        self.task = make_task('Task', self.board, self.owner)
        self.url = f'/api/tasks/{self.task.id}/'

    def test_member_can_get_task(self):  # Ein Board-Mitglied kann eine einzelne Task abrufen.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.member))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Task')

    def test_outsider_get_returns_403(self):  # Ein Nicht-Mitglied kann eine Task nicht abrufen und erhält 403.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.outsider))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_can_patch_task(self):  # Ein Board-Mitglied kann den Titel einer Task per PATCH ändern.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.member))
        response = self.client.patch(self.url, {'title': 'Updated'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated')

    def test_patch_reviewer_not_member_returns_400(self):  # Ein Reviewer, der kein Board-Mitglied ist, wird beim PATCH mit 400 abgelehnt.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.patch(self.url, {'reviewer_id': self.outsider.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_assignee_not_member_returns_400(self):  # Ein Assignee, der kein Board-Mitglied ist, wird beim PATCH mit 400 abgelehnt.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.patch(self.url, {'assignee_id': self.outsider.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_valid_reviewer_returns_200(self):  # Ein Reviewer, der Board-Mitglied ist, kann per PATCH gültig zugewiesen werden.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.patch(self.url, {'reviewer_id': self.member.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_owner_can_delete_task(self):  # Der Board-Owner kann eine Task löschen und erhält 204.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_creator_who_is_not_board_owner_can_delete(self):  # Der Ersteller einer Task kann sie löschen, auch wenn er nicht Board-Owner ist.
        member_task = make_task('MemberTask', self.board, self.member)
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.member))
        response = self.client.delete(f'/api/tasks/{member_task.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_member_non_creator_delete_returns_403(self):  # Ein Mitglied, das die Task nicht erstellt hat, kann sie nicht löschen.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.member))
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_outsider_delete_returns_403(self):  # Ein Nicht-Mitglied kann eine Task nicht löschen und erhält 403.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.outsider))
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_task_with_null_board_denies_access(self):  # Eine Task ohne zugeordnetes Board verweigert den Zugriff mit 403.
        orphan = DashboardTasks.objects.create(title='Orphan', description='D')
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.get(f'/api/tasks/{orphan.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nonexistent_task_returns_404(self):  # Anfrage auf eine nicht existierende Task-ID gibt 404 zurück.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.get('/api/tasks/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_returns_401(self):  # Unauthentifizierte Anfrage auf eine einzelne Task gibt 401 zurück.
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_task_without_board_skips_member_validation(self):  # PATCH auf eine boardlose Task schlägt mit 403 fehl, da kein Board-Kontext existiert.
        orphan = DashboardTasks.objects.create(title='Orphan', description='D')
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.patch(f'/api/tasks/{orphan.id}/', {'title': 'X'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AssignedTaskViewTests(APITestCase):  # Testet GET /api/tasks/assigned-to-me/.
    url = '/api/tasks/assigned-to-me/'

    def setUp(self):  # Legt zwei Nutzer, ein Board und je eine zugewiesene Task pro Nutzer an.
        self.user = make_user('user', 'user@example.com')
        self.other = make_user('other', 'other@example.com')
        self.board = make_board('Board', self.user, members=[self.other])
        make_task('Mine', self.board, self.user, assignee=self.user)
        make_task('Theirs', self.board, self.other, assignee=self.other)

    def test_returns_only_tasks_assigned_to_me(self):  # Nur Tasks, die dem eingeloggten User zugewiesen sind, werden zurückgegeben.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.user))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Mine')

    def test_empty_result_when_none_assigned(self):  # Ein User ohne zugewiesene Tasks erhält eine leere Liste.
        user2 = make_user('user2', 'user2@example.com')
        Token.objects.get_or_create(user=user2)
        self.client.credentials(HTTP_AUTHORIZATION=auth(user2))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_unauthenticated_returns_401(self):  # Unauthentifizierte Anfrage auf zugewiesene Tasks gibt 401 zurück.
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ReviewerTaskViewTests(APITestCase):  # Testet GET /api/tasks/reviewing/.
    url = '/api/tasks/reviewing/'

    def setUp(self):  # Legt zwei Nutzer, ein Board und je eine Reviewer-Task pro Nutzer an.
        self.user = make_user('user', 'user@example.com')
        self.other = make_user('other', 'other@example.com')
        self.board = make_board('Board', self.user, members=[self.other])
        make_task('Reviewing', self.board, self.user, reviewer=self.user)
        make_task('NotReviewing', self.board, self.other, reviewer=self.other)

    def test_returns_only_tasks_where_i_am_reviewer(self):  # Nur Tasks, bei denen der eingeloggte User Reviewer ist, werden zurückgegeben.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.user))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Reviewing')

    def test_unauthenticated_returns_401(self):  # Unauthentifizierte Anfrage auf Reviewer-Tasks gibt 401 zurück.
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TaskCommentsViewTests(APITestCase):  # Testet GET und POST /api/tasks/<id>/comments/.
    def setUp(self):  # Legt Owner, Mitglied, Außenseiter, Board und eine Testtask an.
        self.owner = make_user('owner', 'owner@example.com')
        self.member = make_user('member', 'member@example.com')
        self.outsider = make_user('outsider', 'outsider@example.com')
        self.board = make_board('Board', self.owner, members=[self.member])
        self.task = make_task('Task', self.board, self.owner)
        self.url = f'/api/tasks/{self.task.id}/comments/'

    def test_member_can_list_comments(self):  # Ein Board-Mitglied kann die Kommentarliste einer Task abrufen.
        Comment.objects.create(task=self.task, content='Hello', author=self.owner)
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.member))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['content'], 'Hello')

    def test_comments_ordered_by_created_at(self):  # Kommentare werden in aufsteigender Reihenfolge nach Erstellungsdatum zurückgegeben.
        Comment.objects.create(task=self.task, content='First', author=self.owner)
        Comment.objects.create(task=self.task, content='Second', author=self.member)
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.get(self.url)
        self.assertEqual(response.data[0]['content'], 'First')

    def test_outsider_list_returns_403(self):  # Ein Nicht-Mitglied kann Kommentare nicht auflisten und erhält 403.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.outsider))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_can_create_comment(self):  # Ein Board-Mitglied kann einen neuen Kommentar zu einer Task erstellen.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.member))
        response = self.client.post(self.url, {'content': 'Nice work!'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Nice work!')

    def test_owner_comment_shows_author_fullname(self):  # Der Autorenname im Kommentar setzt sich korrekt aus Vor- und Nachname zusammen.
        owner_named = make_user('named', 'named@example.com', 'Alice', 'Smith')
        board = make_board('B2', owner_named)
        task = make_task('T', board, owner_named)
        self.client.credentials(HTTP_AUTHORIZATION=auth(owner_named))
        self.client.post(f'/api/tasks/{task.id}/comments/', {'content': 'Hi'}, format='json')
        response = self.client.get(f'/api/tasks/{task.id}/comments/')
        self.assertEqual(response.data[0]['author'], 'Alice Smith')

    def test_outsider_create_returns_403(self):  # Ein Nicht-Mitglied kann keinen Kommentar erstellen und erhält 403.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.outsider))
        response = self.client.post(self.url, {'content': 'Hi'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_task_without_board_get_returns_403(self):  # GET auf Kommentare einer Task ohne Board gibt 403 zurück.
        orphan = DashboardTasks.objects.create(title='Orphan', description='D')
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.get(f'/api/tasks/{orphan.id}/comments/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_task_without_board_post_returns_403(self):  # POST auf Kommentare einer Task ohne Board gibt 403 zurück.
        orphan = DashboardTasks.objects.create(title='Orphan', description='D')
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.post(f'/api/tasks/{orphan.id}/comments/', {'content': 'X'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_nonexistent_task_returns_404(self):  # Kommentarliste einer nicht existierenden Task gibt 404 zurück.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.get('/api/tasks/99999/comments/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_returns_401(self):  # Unauthentifizierte Anfrage auf Kommentare gibt 401 zurück.
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CommentSingleViewTests(APITestCase):  # Testet GET, PATCH und DELETE /api/tasks/<id>/comments/<id>/.
    def setUp(self):  # Legt Owner, Mitglied, Außenseiter, Board, Task und einen Testkommentar an.
        self.owner = make_user('owner', 'owner@example.com')
        self.member = make_user('member', 'member@example.com')
        self.outsider = make_user('outsider', 'outsider@example.com')
        self.board = make_board('Board', self.owner, members=[self.member])
        self.task = make_task('Task', self.board, self.owner)
        self.comment = Comment.objects.create(
            task=self.task, content='Hello', author=self.owner
        )
        self.url = f'/api/tasks/{self.task.id}/comments/{self.comment.id}/'

    def test_member_can_get_comment(self):  # Ein Board-Mitglied kann einen einzelnen Kommentar abrufen.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.member))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], 'Hello')

    def test_outsider_get_returns_403(self):  # Ein Nicht-Mitglied kann einen Kommentar nicht abrufen und erhält 403.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.outsider))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_author_can_patch_comment(self):  # Der Autor kann seinen Kommentar per PATCH bearbeiten.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.patch(self.url, {'content': 'Updated'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], 'Updated')

    def test_non_author_patch_returns_403(self):  # Ein Board-Mitglied, das nicht Autor ist, kann den Kommentar nicht bearbeiten.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.member))
        response = self.client.patch(self.url, {'content': 'Hacked'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_author_can_delete_comment(self):  # Der Autor kann seinen Kommentar löschen, er existiert danach nicht mehr.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(id=self.comment.id).exists())

    def test_non_author_delete_returns_403(self):  # Ein Nicht-Autor kann den Kommentar nicht löschen und erhält 403.
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.member))
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_comment_on_task_without_board_get_returns_403(self):  # Ein Kommentar einer boardlosen Task verweigert den Zugriff mit 403.
        orphan_task = DashboardTasks.objects.create(title='Orphan', description='D')
        orphan_comment = Comment.objects.create(
            task=orphan_task, content='Orphan comment', author=self.owner
        )
        self.client.credentials(HTTP_AUTHORIZATION=auth(self.owner))
        response = self.client.get(
            f'/api/tasks/{orphan_task.id}/comments/{orphan_comment.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_returns_401(self):  # Unauthentifizierte Anfrage auf einen einzelnen Kommentar gibt 401 zurück.
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
