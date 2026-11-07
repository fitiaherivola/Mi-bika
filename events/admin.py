from django.contrib import admin
from .models import Evenement, Notification


@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    pass  # affichage par défaut, on personnalisera après


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    pass
