from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HumeurViewSet, NotationViewSet

router = DefaultRouter()
router.register(r'humeurs', HumeurViewSet)
router.register(r'notations', NotationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
