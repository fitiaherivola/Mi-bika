from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ('username', 'email', 'style_prefere', 'morphologie', 'is_staff')
    list_filter  = ('style_prefere', 'morphologie', 'teint_avatar', 'is_staff')
    search_fields = ('username', 'email')

    # Ajoute tes champs perso dans le formulaire admin
    fieldsets = UserAdmin.fieldsets + (
        ('Profil Mi-bika', {
            'fields': ('style_prefere', 'teint_avatar', 'morphologie')
        }),
    )
