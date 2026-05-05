from rest_framework import serializers
from .models import Evenement, Notification


class EvenementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evenement
        fields = ['id', 'titre', 'description', 'date_event', 'tenue_reservee', 'utilisateur', 'date_creation']
        read_only_fields = ['date_creation']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'titre', 'contenu', 'est_lue', 'date_envoi', 'evenement', 'utilisateur']
        read_only_fields = ['date_envoi']
