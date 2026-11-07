from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication, SessionAuthentication

from users.models import Utilisateur
from wardrobe.models import Vetement, Contrainte
from wardrobe.serializers import VetementSerializer, ContrainteSerializer
from wardrobe.services.base import (
    get_vetements_utilisateur,
    get_vetement_par_id,
    creer_vetement,
    modifier_vetement,
    supprimer_vetement,
    marquer_sale,
    marquer_propre,
    stats_garde_robe,
    vetements_disponibles_pour_tenue,
    rechercher_vetements,
)
from wardrobe.services.optimise import (
    rechercher_vetements_trie,
    trier_vetements_avl,
    suggerer_remplacement,
    comparer_recherche,
)


class ListeVetementsView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        vetements = get_vetements_utilisateur(request.user)
        return Response(VetementSerializer(vetements, many=True).data)

    def post(self, request):
        serializer = VetementSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        vetement = creer_vetement(
            utilisateur=request.user,
            nom=serializer.validated_data['nom'],
            categorie=serializer.validated_data['categorie'],
            couleur_hex=serializer.validated_data.get('couleur_hex'),
            saison=serializer.validated_data.get('saison', 'TOUTES_SAISONS'),
            style=serializer.validated_data.get('style'),
            image_calque_url=serializer.validated_data.get('image_calque_url'),
        )
        return Response(VetementSerializer(vetement).data,
                        status=status.HTTP_201_CREATED)


class DetailVetementView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        vetement = get_vetement_par_id(pk, request.user)
        if not vetement:
            return Response({'erreur': 'Vêtement introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(VetementSerializer(vetement).data)

    def put(self, request, pk):
        vetement = get_vetement_par_id(pk, request.user)
        if not vetement:
            return Response({'erreur': 'Vêtement introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = VetementSerializer(vetement, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        vetement = modifier_vetement(pk, request.user,
                                     **serializer.validated_data)
        return Response(VetementSerializer(vetement).data)

    def patch(self, request, pk):
        vetement = get_vetement_par_id(pk, request.user)
        if not vetement:
            return Response({'erreur': 'Vêtement introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        vetement = modifier_vetement(pk, request.user, **request.data)
        return Response(VetementSerializer(vetement).data)

    def delete(self, request, pk):
        supprime = supprimer_vetement(pk, request.user)
        if not supprime:
            return Response({'erreur': 'Vêtement introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RechercheVetementsView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        terme = request.query_params.get('q', '').strip()
        mode  = request.query_params.get('mode', 'baseline')
        if not terme:
            return Response({'erreur': 'Paramètre q requis.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if mode == 'trie':
            resultats = rechercher_vetements_trie(request.user, terme)
        else:
            resultats = rechercher_vetements(request.user, terme)
        return Response(VetementSerializer(resultats, many=True).data)


class ComparerRechercheView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        terme = request.query_params.get('q', '').strip()
        if not terme:
            return Response({'erreur': 'Paramètre q requis.'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(comparer_recherche(request.user, terme))


class TriVetementsAVLView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        resultats = trier_vetements_avl(request.user)
        return Response([
            {'score': score, 'vetement': VetementSerializer(v).data}
            for score, v in resultats
        ])


class MarquerSaleView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        vetement = marquer_sale(pk, request.user)
        if not vetement:
            return Response({'erreur': 'Vêtement introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(VetementSerializer(vetement).data)


class MarquerPropreView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        vetement = marquer_propre(pk, request.user)
        if not vetement:
            return Response({'erreur': 'Vêtement introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(VetementSerializer(vetement).data)


class SuggererRemplacementView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        vetement = get_vetement_par_id(pk, request.user)
        if not vetement:
            return Response({'erreur': 'Vêtement introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        remplacement = suggerer_remplacement(vetement, request.user)
        if not remplacement:
            return Response({'erreur': 'Aucun remplacement disponible.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(VetementSerializer(remplacement).data)


class StatsGardeRobeView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(stats_garde_robe(request.user))


class VetementsPourTenueView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        saison = request.query_params.get('saison')
        style  = request.query_params.get('style')
        result = vetements_disponibles_pour_tenue(
            request.user, saison=saison, style=style
        )
        return Response({
            'hauts':       VetementSerializer(result['hauts'], many=True).data,
            'bas':         VetementSerializer(result['bas'], many=True).data,
            'accessoires': VetementSerializer(result['accessoires'], many=True).data,
            'suffisant':   result['suffisant'],
        })


# ═══════════════════════════════════════════════════════════════
# CONTRAINTES PERSONNELLES
# ═══════════════════════════════════════════════════════════════


class ListeContraintesView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        contraintes = Contrainte.objects.filter(utilisateur=request.user).order_by('-priorite')
        return Response(ContrainteSerializer(contraintes, many=True).data)


class CreerContrainteView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ContrainteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save(utilisateur=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DetailContrainteView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            contrainte = Contrainte.objects.get(pk=pk, utilisateur=request.user)
        except Contrainte.DoesNotExist:
            return Response({'erreur': 'Contrainte introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(ContrainteSerializer(contrainte).data)

    def patch(self, request, pk):
        try:
            contrainte = Contrainte.objects.get(pk=pk, utilisateur=request.user)
        except Contrainte.DoesNotExist:
            return Response({'erreur': 'Contrainte introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = ContrainteSerializer(contrainte, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        try:
            contrainte = Contrainte.objects.get(pk=pk, utilisateur=request.user)
        except Contrainte.DoesNotExist:
            return Response({'erreur': 'Contrainte introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        contrainte.delete()
        return Response({'message': 'Contrainte supprimée.'},
                        status=status.HTTP_204_NO_CONTENT)


# Palette visuelle pour BF3
PALETTE_COULEURS = [
    {'nom': 'Blanc', 'hex': '#FFFFFF'},
    {'nom': 'Noir', 'hex': '#000000'},
    {'nom': 'Bleu marine', 'hex': '#000080'},
    {'nom': 'Rouge', 'hex': '#FF0000'},
    {'nom': 'Beige', 'hex': '#F5F5DC'},
    {'nom': 'Gris', 'hex': '#C0C0C0'},
    {'nom': 'Or', 'hex': '#FFD700'},
    {'nom': 'Vert foncé', 'hex': '#2F4F4F'},
    {'nom': 'Bordeaux', 'hex': '#8B0000'},
    {'nom': 'Jaune', 'hex': '#FFFF00'},
    {'nom': 'Marron', 'hex': '#8B4513'},
    {'nom': 'Rose', 'hex': '#FFC0CB'},
]


class PaletteCouleursView(APIView):
    """
    GET /api/wardrobe/palette/
    Palette de couleurs pour associer aux vêtements (BF3).
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({
            'couleurs': PALETTE_COULEURS,
            'total': len(PALETTE_COULEURS),
        })
