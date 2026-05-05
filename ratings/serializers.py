from rest_framework import serializers
from .models import Humeur


class HumeurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Humeur
        fields = ['id', 'type_humeur', 'date_saisie', 'utilisateur']
        read_only_fields = ['date_saisie']
