from django.contrib import admin
from .models import Tenue


@admin.register(Tenue)
class TenueAdmin(admin.ModelAdmin):
    list_display = ('id', 'utilisateur', 'score_harmonie', 'date_creation')
    list_filter = ('score_harmonie', 'utilisateur', 'date_creation')
    search_fields = ('utilisateur__pseudo',)
    readonly_fields = ('date_creation',)
