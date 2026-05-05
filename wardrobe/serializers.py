# REMPLACER par
from rest_framework import serializers
from .models import Vetement

class VetementSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Vetement
        fields = ['id', 'nom', 'categorie', 'couleur_hex',
                  'est_propre', 'saison', 'style',
                  'image_calque_url', 'utilisateur']