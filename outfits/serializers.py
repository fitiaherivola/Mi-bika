from rest_framework import serializers
from .models import Tenue
from wardrobe.models import Vetement


class VetementMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vetement
        fields = ['id', 'nom', 'categorie', 'couleur_hex', 'style', 'saison', 'image_calque_url']


class TenueSerializer(serializers.ModelSerializer):
    haut_detail       = VetementMiniSerializer(source='haut',       read_only=True)
    bas_detail        = VetementMiniSerializer(source='bas',        read_only=True)
    accessoire_detail = VetementMiniSerializer(source='accessoire', read_only=True)

    class Meta:
        model = Tenue
        fields = [
            'id', 'utilisateur',
            'haut', 'bas', 'accessoire',
            'haut_detail', 'bas_detail', 'accessoire_detail',
            'score_harmonie', 'algorithme', 'date_creation',
        ]
        read_only_fields = ['date_creation']
