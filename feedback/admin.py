from django.contrib import admin
from .models import FeedbackMessage


@admin.register(FeedbackMessage)
class FeedbackMessageAdmin(admin.ModelAdmin):
    list_display = ('sujet', 'statut', 'utilisateur', 'date_creation')
    list_filter = ('statut', 'date_creation')
    search_fields = ('sujet', 'message', 'utilisateur__username')
    readonly_fields = ('date_creation',)