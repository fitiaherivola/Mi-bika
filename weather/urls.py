from django.urls import path
from weather.views import (
    MeteoduJourView,
    HistoriqueMeteoView,
    EnregistrerMeteoView,
    ContraintesMeteoView,
    StatsMeteoView,
)

urlpatterns = [
    path('aujourd-hui/',  MeteoduJourView.as_view()),
    path('historique/',   HistoriqueMeteoView.as_view()),
    path('enregistrer/',  EnregistrerMeteoView.as_view()),
    path('contraintes/',  ContraintesMeteoView.as_view()),
    path('stats/',        StatsMeteoView.as_view()),
]