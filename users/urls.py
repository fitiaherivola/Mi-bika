from django.urls import path
from .views import CreerUtilisateurView, ListeUtilisateursView, ProfilView

urlpatterns = [
    path('',          ListeUtilisateursView.as_view()),
    path('creer/',    CreerUtilisateurView.as_view()),
    path('<int:pk>/', ProfilView.as_view()),
]