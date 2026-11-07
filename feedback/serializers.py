from rest_framework import serializers
from .models import FeedbackMessage


class FeedbackMessageSerializer(serializers.ModelSerializer):
    statut_display = serializers.CharField(
        source='get_statut_display', read_only=True
    )
    utilisateur_display = serializers.CharField(
        source='utilisateur.username', read_only=True
    )
    date_creation_display = serializers.DateTimeField(
        source='date_creation', read_only=True,
        format='%d/%m/%Y %H:%M'
    )

    class Meta:
        model = FeedbackMessage
        fields = [
            'id', 'sujet', 'message', 'statut', 'statut_display',
            'utilisateur', 'utilisateur_display',
            'date_creation', 'date_creation_display',
        ]
        read_only_fields = ('id', 'date_creation', 'utilisateur')


class FeedbackMessageUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackMessage
        fields = ['statut']