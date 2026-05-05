from django.urls import path
from wardrobe.views import (
    ListeVetementsView,
    DetailVetementView,
    RechercheVetementsView,
    ComparerRechercheView,
    TriVetementsAVLView,
    MarquerSaleView,
    MarquerPropreView,
    SuggererRemplacementView,
    StatsGardeRobeView,
    VetementsPourTenueView,
)

urlpatterns = [
    path('',                          ListeVetementsView.as_view()),
    path('<int:pk>/',                 DetailVetementView.as_view()),
    path('recherche/',                RechercheVetementsView.as_view()),
    path('recherche/comparer/',       ComparerRechercheView.as_view()),
    path('trier/',                    TriVetementsAVLView.as_view()),
    path('stats/',                    StatsGardeRobeView.as_view()),
    path('disponibles/',              VetementsPourTenueView.as_view()),
    path('<int:pk>/sale/',            MarquerSaleView.as_view()),
    path('<int:pk>/propre/',          MarquerPropreView.as_view()),
    path('<int:pk>/remplacer/',       SuggererRemplacementView.as_view()),
]