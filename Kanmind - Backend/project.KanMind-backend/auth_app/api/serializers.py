from django.contrib.auth.models import User
from django.db import transaction
from django.contrib.auth import authenticate
from rest_framework import serializers

def validate_registration_data(data):                                                # Überprüfe die Registrierungsdaten.
    
    if data['password'] != data['repeated_password']:                                # Stimen password un repeated_password' überein?
        raise serializers.ValidationError({'password': 'Passwords do not match'})
    if User.objects.filter(email=data['email']).exists():                            # Überprüfe, ob die E-Mail bereits existiert.
        raise serializers.ValidationError({'email': 'Email already exists'})
    return data


def split_full_name(full_name):                                                      # Teile den vollständigen Namen in Vor- und Nachname auf.
    
    parts = full_name.strip().split(" ", 1)                                          # Wenn nur ein Name angegeben wurde, wird der Nachname auf einen leeren String gesetzt
    first_name = parts[0]
    if len(parts) > 1:
            last_name = parts[1]
    else:
        last_name = ""
    return first_name, last_name


def generate_username(first_name, last_name):                                         # Erzeugteinen eindeutigen Benutzernamen aus Vor- und Nachname.
    
    base_username = f"{first_name.lower()}.{last_name.lower()}"                       # Format: first.last
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():                            # Wenn der Benutzername bereits existiert, wird eine Zahl angehängt, um einen eindeutigen Benutzernamen zu erstellen.
        username = f"{base_username}{counter}"
        counter += 1
    return username


def create_user(validated_data):                                                      # Neuer Benutzer in der Datenbank erstellen.
    
    fullname = validated_data.pop('fullname')
    validated_data.pop('repeated_password')
    first_name, last_name = split_full_name(fullname)                               # Extrahiere 'fullname' und teile ihn in Vor- und Nachname auf.
    username = generate_username(first_name, last_name)                             # Erzeuge einen eindeutigen Benutzernamen aus Vor- und Nachname.
    with transaction.atomic():                                                      # Speichere den Benutzer mit einem verschlüsselten Passwort mit transaction.atomic().
        user = User(
            email=validated_data['email'],
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        user.set_password(validated_data['password'])
        user.save()
    return user

class RegisterationSerializer(serializers.ModelSerializer):                         # Serializer für die Benutzerregistrierung
    
    repeated_password = serializers.CharField(write_only=True)
    fullname = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['id', 'fullname', 'email', 'password', 'repeated_password']       # Eingabe notwendig: fullname, email, password, repeated_password
        extra_kwargs = {
            'password' :  {
                'write_only' : True
            }
        }

    def validate(self, data):                                                       # Prüft die Eingaben und erstellt einen neuen Benutzer.
        return validate_registration_data(data)
    
    def create(self, validated_data):
        return create_user(validated_data)

class UserLoginSerializer(serializers.Serializer):                                  # Serializer für die Benutzeranmeldung.
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    def validate(self, data):
      
        email = data.get('email')                                                   # Eingabe notwendig: email, password
        password = data.get('password')
        try:                                                                        # Prüft die Anmeldedaten und authentifiziert den Benutzer.
            user = User.objects.get(email=email)
        except User.DoesNotExist:                                                   # Fehler, wenn die E-Mail nicht existiert.
            raise serializers.ValidationError("Ungültige E-mail")
        user = authenticate(username=user.username, password=password)
        if not user:                                                                # Fehler, wenn das Passwort falsch ist.
            raise serializers.ValidationError("Passwort ist falsch")
        data['user'] = user                                                         # Füge authentifiziertenBenutze zu data['user'] hinzu.
        return data