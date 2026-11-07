from rest_framework import serializers
from .models import Evenement, Notification, Calendrier
from outfits.serializers import TenueSerializer
from users.models import Utilisateur


class EvenementSerializer(serializers.ModelSerializer):
    utilisateur = serializers.PrimaryKeyRelatedField(read_only=True)
    type_evt_display = serializers.CharField(
        source='get_type_evt_display', read_only=True
    )
    tenue_reservee_detail = TenueSerializer(source='tenue_reservee', read_only=True)

    class Meta:
        model = Evenement
        fields = [
            'id', 'nom_evt', 'type_evt', 'type_evt_display',
            'date_evt', 'lieu', 'tenue_reservee', 'tenue_reservee_detail', 'calendrier', 'utilisateur',
        ]

    def validate_date_evt(self, value):
        if value is None:
            return value
        from django.utils import timezone
        if timezone.is_naive(value):
            return timezone.make_aware(value, timezone.get_current_timezone())
        return value

    def validate(self, data):
        utilisateur = data.get('utilisateur')
        if utilisateur and not Utilisateur.objects.filter(id=utilisateur.id).exists():
            raise serializers.ValidationError({"utilisateur": "Cet utilisateur n'existe pas."})

        tenue_reservee = data.get('tenue_reservee')
        if tenue_reservee and not Tenue.objects.filter(id=tenue_reservee.id).exists():
            raise serializers.ValidationError({"tenue_reservee": "Cette tenue réservée n'existe pas."})

        calendrier = data.get('calendrier')
        if calendrier and not Calendrier.objects.filter(id=calendrier.id).exists():
            raise serializers.ValidationError({"calendrier": "Ce calendrier n'existe pas."})

        return data


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer pour les notifications intelligentes (événements, météo, suggestions)."""
    type_notif_display = serializers.CharField(source='get_type_notif_display', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'contenu', 'type_notif', 'type_notif_display', 
                  'est_lue', 'date_envoi', 'evenement', 'utilisateur']
        read_only_fields = ['date_envoi']
