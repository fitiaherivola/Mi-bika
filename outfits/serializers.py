from rest_framework import serializers
from .models import Tenue


class TenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenue
        fields = ['id', 'utilisateur', 'haut', 'bas', 'accessoire', 'score_harmonie', 'date_creation']
        read_only_fields = ['date_creation']
