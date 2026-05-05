from django.contrib import admin
from .models import Vetement


@admin.register(Vetement)
class VetementAdmin(admin.ModelAdmin):
    list_display    = ('nom', 'categorie', 'style', 'saison', 'est_propre')
    list_filter     = ('categorie', 'style', 'saison', 'est_propre')
    search_fields   = ('nom',)
