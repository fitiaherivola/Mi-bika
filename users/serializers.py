from rest_framework import serializers
from .models import Utilisateur


class UtilisateurSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Utilisateur
        fields = ['id', 'pseudo', 'style_prefere',
                  'teint_avatar', 'morphologie']


class CreateUtilisateurSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Utilisateur
        fields = ['pseudo', 'style_prefere',
                  'teint_avatar', 'morphologie']