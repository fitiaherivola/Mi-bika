from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HumeurViewSet

router = DefaultRouter()
router.register(r'humeurs', HumeurViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
