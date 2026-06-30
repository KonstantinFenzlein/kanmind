from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.generics import GenericAPIView
from .serializers import RegisterationSerializer, UserLoginSerializer

class RegisterView(APIView):
    # API-Endpunkt für die Benutzerregistrierung.
    # - Erlaubt jedem Benutzer den Zugriff (keine Authentifizierung erforderlich)
    # - Akzeptiert POST-Request mit: fullname, email, password, repeated_password
    # - Gibt bei erfolgreicher Registrierung Token und Benutzerinformationen zurück
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = RegisterationSerializer(data=request.data)
        if serializer.is_valid():
            saved_account = serializer.save()
            token, created = Token.objects.get_or_create(user=saved_account)
            data = {
                'token' : token.key,
                'fullname': f"{saved_account.first_name} {saved_account.last_name}".strip(),
                'user_id': saved_account.pk,
                'email' : saved_account.email
            }
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(GenericAPIView):
    # API-Endpunkt für die Benutzeranmeldung.
    # - Erlaubt jedem Benutzer den Zugriff (keine Authentifizierung erforderlich)
    # - Akzeptiert POST-Request mit E-Mail und Passwort
    # - Gibt bei Erfolg Authentifizierungs-Token und Benutzerinformationen zurück

    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = {}
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        data = {
            'token' : token.key,
            'fullname': f"{user.first_name} {user.last_name}".strip(),
            'user_id': user.pk,
            'email' : user.email
            }
        return Response(data)
    

class LogoutView(APIView):
    # API-Endpunkt zum Abmelden eines authentifizierten Benutzers.
    # - Erfordert Authentifizierung
    # - Löscht den Token des Benutzers

    def post(self, request):
        request.user.auth_token.delete()
        return Response({"detail": "Logout erfolgreich. Token wurde gelöscht."}, status=status.HTTP_200_OK)