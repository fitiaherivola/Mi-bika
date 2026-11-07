# REMPLACER par
from rest_framework import serializers
from .models import Vetement, Contrainte

class VetementSerializer(serializers.ModelSerializer):
    last_worn_display = serializers.DateTimeField(
        source='last_worn', read_only=True,
        format='%d/%m/%Y %H:%M', default=None
    )

    class Meta:
        model  = Vetement
        fields = ['id', 'nom', 'categorie', 'couleur_hex',
                  'est_propre', 'is_worn', 'last_worn',
                  'last_worn_display', 'saison', 'style',
                  'image_calque_url', 'utilisateur']
        read_only_fields = ['utilisateur']


class ContrainteSerializer(serializers.ModelSerializer):
    """Serializer pour les contraintes personnelles."""
    type_contrainte_display = serializers.CharField(source='get_type_contrainte_display', read_only=True)

    class Meta:
        model = Contrainte
        fields = ['id', 'type_contrainte', 'type_contrainte_display', 
                  'date_activation', 'priorite', 'utilisateur']
        read_only_fields = ['utilisateur']