from rest_framework import serializers
from .models import Tendance, Boutique


class TendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tendance
        fields = [
            'id', 'titre', 'description', 'style', 'popularite',
            'image_url', 'date_creation', 'date_fin',
        ]
        read_only_fields = ['date_creation']

class BoutiqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Boutique
        fields = ['id', 'nom', 'description', 'style_dominant', 'adresse', 'instagram_url', 'image_url', 'popularite']
