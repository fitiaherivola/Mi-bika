from django.contrib import admin
from .models import Evenement, Notification


@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ('titre', 'utilisateur', 'date_event', 'date_creation')
    list_filter = ('utilisateur', 'date_event', 'date_creation')
    search_fields = ('titre', 'utilisateur__pseudo')
    readonly_fields = ('date_creation',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('titre', 'utilisateur', 'est_lue', 'date_envoi')
    list_filter = ('est_lue', 'utilisateur', 'date_envoi')
    search_fields = ('titre', 'utilisateur__pseudo')
    readonly_fields = ('date_envoi',)
