from django.urls import path
from outfits.views import (
    GenererTenueBaselineView,
    GenererTenueOptimiseView,
    GenererTenueDijkstraView,
    GenererTenueBacktrackingView,
    ComparerAlgorithmesView,
    ComparerDijkstraView,
    RecommandationKNNView,
    RecommandationMLPView,
    ListeTenuesView,
    DetailTenueView,
)

urlpatterns = [
    path('',                     ListeTenuesView.as_view()),
    path('<int:pk>/',            DetailTenueView.as_view()),
    path('generer/baseline/',    GenererTenueBaselineView.as_view()),
    path('generer/optimise/',    GenererTenueOptimiseView.as_view()),
    path('generer/dijkstra/',    GenererTenueDijkstraView.as_view()),
    path('generer/backtracking/', GenererTenueBacktrackingView.as_view()),
    path('comparer/',            ComparerAlgorithmesView.as_view()),
    path('comparer/dijkstra/',   ComparerDijkstraView.as_view()),
    path('recommander/',         RecommandationKNNView.as_view()),
    path('recommander/mlp/',     RecommandationMLPView.as_view()),
]