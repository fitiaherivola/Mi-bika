from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EvenementViewSet, NotificationViewSet

router = DefaultRouter()
router.register(r'evenements', EvenementViewSet)
router.register(r'notifications', NotificationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
