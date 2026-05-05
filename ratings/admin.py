from django.contrib import admin
from .models import Humeur


@admin.register(Humeur)
class HumeurAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'type_humeur', 'date_saisie')
    list_filter = ('type_humeur', 'utilisateur', 'date_saisie')
    search_fields = ('utilisateur__pseudo',)
    readonly_fields = ('date_saisie',)
