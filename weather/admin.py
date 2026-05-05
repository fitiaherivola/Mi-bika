from django.contrib import admin
from .models import Meteo


@admin.register(Meteo)
class MeteoAdmin(admin.ModelAdmin):
    list_display    = ('ville', 'temperature', 'condition', 'date_prediction')
    list_filter     = ('ville', 'condition', 'date_prediction')
    search_fields   = ('ville',)
    readonly_fields = ('derniere_maj',)