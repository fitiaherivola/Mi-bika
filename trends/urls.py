from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TendanceViewSet, DashboardTendancesView, BoutiqueViewSet

router = DefaultRouter()
router.register(r'tendances', TendanceViewSet)
router.register(r'boutiques', BoutiqueViewSet)

urlpatterns = [
    path('dashboard/', DashboardTendancesView.as_view()),
    path('', include(router.urls)),
]
