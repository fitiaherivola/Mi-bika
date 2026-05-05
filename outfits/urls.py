from django.urls import path
from outfits.views import (
    GenererTenueBaselineView,
    GenererTenueOptimiseView,
    ComparerAlgorithmesView,
    RecommandationKNNView,
    ListeTenuesView,
    DetailTenueView,
)

urlpatterns = [
    path('',                     ListeTenuesView.as_view()),
    path('<int:pk>/',            DetailTenueView.as_view()),
    path('generer/baseline/',    GenererTenueBaselineView.as_view()),
    path('generer/optimise/',    GenererTenueOptimiseView.as_view()),
    path('comparer/',            ComparerAlgorithmesView.as_view()),
    path('recommander/',         RecommandationKNNView.as_view()),
]