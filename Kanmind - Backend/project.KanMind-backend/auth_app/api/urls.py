from django.urls import path
from .views import RegisterView, UserLoginView, LogoutView

# ------------------------------
# Authentifizierungs-Endpunkte
# ------------------------------

urlpatterns = [
    path('registration/', RegisterView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]