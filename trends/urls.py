from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TendanceViewSet

router = DefaultRouter()
router.register(r'tendances', TendanceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
