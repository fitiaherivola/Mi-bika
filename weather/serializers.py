from rest_framework import serializers
from .models import Meteo


class MeteoSerializer(serializers.ModelSerializer):
    saison_estimee = serializers.SerializerMethodField()

    class Meta:
        model  = Meteo
        fields = ['id', 'ville', 'temperature', 'condition',
                  'date_prediction', 'derniere_maj', 'saison_estimee']
        read_only_fields = ['derniere_maj', 'saison_estimee']

    def get_saison_estimee(self, obj):
        return obj.saison_estimee()
