from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class RegisterViewTests(APITestCase):  # Testet POST /api/registration/.
    url = '/api/registration/'

    def _post(self, fullname='John Doe', email='john@example.com',  # Hilfsmethode: sendet einen Registrierungs-POST mit Standard- oder überschriebenen Werten.
               password='StrongPass1', repeated_password='StrongPass1'):
        return self.client.post(self.url, {
            'fullname': fullname,
            'email': email,
            'password': password,
            'repeated_password': repeated_password,
        }, format='json')

    def test_successful_registration_returns_token_and_user_data(self):  # Erfolgreiche Registrierung gibt 201 mit Token, user_id, Email und vollständigem Namen zurück.
        response = self._post()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertIn('user_id', response.data)
        self.assertEqual(response.data['email'], 'john@example.com')
        self.assertEqual(response.data['fullname'], 'John Doe')

    def test_registration_single_name_sets_empty_last_name(self):  # Einwortiger Name führt zu leerem Nachname im User-Objekt.
        response = self._post(fullname='Singlename', email='single@example.com')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['fullname'], 'Singlename')
        user = User.objects.get(email='single@example.com')
        self.assertEqual(user.last_name, '')

    def test_registration_creates_token(self):  # Nach der Registrierung existiert ein Token für den neuen User in der Datenbank.
        self._post()
        user = User.objects.get(email='john@example.com')
        self.assertTrue(Token.objects.filter(user=user).exists())

    def test_password_mismatch_returns_400(self):  # Unterschiedliche Passwörter führen zu einem Validierungsfehler mit 400.
        response = self._post(repeated_password='Different1')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_duplicate_email_returns_400(self):  # Eine bereits registrierte E-Mail wird mit 400 und einem Fehlerfeld abgelehnt.
        User.objects.create_user(username='existing', email='john@example.com', password='pass')
        response = self._post()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_missing_fields_returns_400(self):  # Eine leere Anfrage ohne Pflichtfelder gibt 400 zurück.
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_name_generates_unique_username(self):  # Gleicher Vor- und Nachname bei mehreren Nutzern erzeugt jeweils eindeutige Benutzernamen.
        self._post(email='john1@example.com')
        self._post(email='john2@example.com')
        self._post(email='john3@example.com')
        users = User.objects.filter(first_name='John', last_name='Doe')
        usernames = list(users.values_list('username', flat=True))
        self.assertEqual(len(set(usernames)), 3)


class LoginViewTests(APITestCase):  # Testet POST /api/login/.
    url = '/api/login/'

    def setUp(self):  # Legt einen Testnutzer mit bekannten Zugangsdaten an.
        self.user = User.objects.create_user(
            username='john.doe',
            email='john@example.com',
            password='StrongPass1',
            first_name='John',
            last_name='Doe',
        )

    def test_successful_login_returns_token_and_user_data(self):  # Gültige Zugangsdaten geben 200 mit Token, Email, vollständigem Namen und user_id zurück.
        response = self.client.post(self.url, {
            'email': 'john@example.com',
            'password': 'StrongPass1',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['email'], 'john@example.com')
        self.assertEqual(response.data['fullname'], 'John Doe')
        self.assertEqual(response.data['user_id'], self.user.pk)

    def test_wrong_password_returns_400(self):  # Ein falsches Passwort wird mit 400 abgelehnt.
        response = self.client.post(self.url, {
            'email': 'john@example.com',
            'password': 'WrongPass',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonexistent_email_returns_400(self):  # Eine nicht registrierte E-Mail führt zu einem 400-Fehler.
        response = self.client.post(self.url, {
            'email': 'nobody@example.com',
            'password': 'StrongPass1',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_email_returns_400(self):  # Eine Anfrage ohne E-Mail-Feld wird mit 400 abgelehnt.
        response = self.client.post(self.url, {'password': 'StrongPass1'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_password_returns_400(self):  # Eine Anfrage ohne Passwort-Feld wird mit 400 abgelehnt.
        response = self.client.post(self.url, {'email': 'john@example.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LogoutViewTests(APITestCase):  # Testet POST /api/logout/.
    url = '/api/logout/'

    def setUp(self):  # Legt einen Testnutzer mit gültigem Auth-Token an.
        self.user = User.objects.create_user(
            username='john.doe',
            email='john@example.com',
            password='StrongPass1',
        )
        self.token = Token.objects.create(user=self.user)

    def test_successful_logout_deletes_token(self):  # Abmeldung mit gültigem Token gibt 200 zurück und löscht den Token aus der Datenbank.
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Token.objects.filter(user=self.user).exists())

    def test_unauthenticated_logout_returns_401(self):  # Abmeldung ohne Token gibt 401 zurück.
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
