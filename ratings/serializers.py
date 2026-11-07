from rest_framework import serializers
from .models import Humeur, Notation


class HumeurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Humeur
        fields = ['id', 'type_humeur', 'date_saisie', 'utilisateur']
        read_only_fields = ['date_saisie']


class NotationSerializer(serializers.ModelSerializer):
    """Serializer pour les notations de tenues (apprentissage des préférences)."""
    note_display = serializers.CharField(source='get_note_display', read_only=True)
    tenue_details = serializers.SerializerMethodField()

    class Meta:
        model = Notation
        fields = ['id', 'note', 'note_display', 'commentaire', 
                  'date_notation', 'est_portee', 'tenue', 'tenue_details', 'utilisateur']
        read_only_fields = ['date_notation']

    def get_tenue_details(self, obj):
        """Retourne les détails minimalistes de la tenue."""
        if obj.tenue:
            return {
                'id': obj.tenue.id,
                'score_harmonie': obj.tenue.score_harmonie,
            }
        return None
