from rest_framework import serializers
from .models import Tendance


class TendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tendance
        fields = ['id', 'titre', 'description', 'popularite', 'date_creation', 'date_fin']
        read_only_fields = ['date_creation']
