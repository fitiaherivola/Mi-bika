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
    ListeContraintesView,
    CreerContrainteView,
    DetailContrainteView,
    PaletteCouleursView,
)

urlpatterns = [
    path('palette/',                  PaletteCouleursView.as_view()),
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
    # Contraintes personnelles
    path('contraintes/',              ListeContraintesView.as_view()),
    path('contraintes/creer/',        CreerContrainteView.as_view()),
    path('contraintes/<int:pk>/',     DetailContrainteView.as_view()),
]