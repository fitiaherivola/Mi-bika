from rest_framework import serializers
from .models import Utilisateur


class UtilisateurSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Utilisateur
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'style_prefere', 'teint_avatar', 'morphologie', 'photo_profil']

    def validate_username(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("L'identifiant ne peut pas être vide.")
        qs = Utilisateur.objects.filter(username__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Cet identifiant est déjà utilisé.")
        return value


class CreateUtilisateurSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model  = Utilisateur
        fields = ['username', 'email', 'password', 'first_name', 'last_name',
                  'style_prefere', 'teint_avatar', 'morphologie', 'photo_profil']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Utilisateur.objects.create_user(**validated_data, password=password)
        return user