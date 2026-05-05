from django.contrib import admin
from .models import Tendance


@admin.register(Tendance)
class TendanceAdmin(admin.ModelAdmin):
    list_display = ('titre', 'popularite', 'date_creation', 'date_fin')
    list_filter = ('popularite', 'date_creation', 'date_fin')
    search_fields = ('titre',)
    readonly_fields = ('date_creation',)
