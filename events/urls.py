from django.urls import path
from django.views.generic import RedirectView
from .views import (
    ListeEvenementsView,
    DetailEvenementView,
    GenererTenuePourEvenementView,
    ListeCalendriersView,
    DetailCalendrierView,
    ListeNotificationsView,
    MarquerLueView,
    NotificationsPourTypeView,
    NotificationsNonLuesView,
)

urlpatterns = [
    path('', RedirectView.as_view(url='evenements/', permanent=False)),
    path('calendriers/',                   ListeCalendriersView.as_view()),
    path('calendriers/<int:pk>/',         DetailCalendrierView.as_view()),
    path('evenements/',                    ListeEvenementsView.as_view()),
    path('evenements/<int:pk>/',           DetailEvenementView.as_view()),
    path('evenements/<int:pk>/generer-tenue/', GenererTenuePourEvenementView.as_view()),
    path('notifications/',                 ListeNotificationsView.as_view()),
    path('notifications/<int:pk>/lue/',    MarquerLueView.as_view()),
    path('notifications/by-type/',         NotificationsPourTypeView.as_view()),
    path('notifications/unread/',          NotificationsNonLuesView.as_view()),
]