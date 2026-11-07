from django.urls import path
from .views import (
    ListeUtilisateursView,
    ProfilView,
    LoginView,
    LogoutView,
    JWTRefreshView,
    ProfilUtilisateurActuelView,
)

urlpatterns = [
    path('',          ListeUtilisateursView.as_view()),      # GET/POST
    path('login/',    LoginView.as_view()),                  # POST
    path('jwt/refresh/', JWTRefreshView.as_view()),          # POST
    path('logout/',   LogoutView.as_view()),                 # POST
    path('me/',       ProfilUtilisateurActuelView.as_view()), # GET/PATCH
    path('<int:pk>/', ProfilView.as_view()),                 # GET/PATCH
]