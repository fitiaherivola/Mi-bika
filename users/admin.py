from django.contrib import admin
from .models import Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):

    list_display  = ('pseudo', 'style_prefere', 'morphologie', 'teint_avatar')
    list_filter   = ('style_prefere', 'morphologie')
    search_fields = ('pseudo',)