from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.models import Utilisateur
from wardrobe.models import Vetement
from wardrobe.serializers import VetementSerializer
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


def get_utilisateur(request):
    """
    Récupère l'utilisateur depuis l'id passé en paramètre.
    Remplace request.user — plus d'AbstractUser.
    """
    uid = (request.data.get('utilisateur_id')
           or request.query_params.get('utilisateur_id'))
    if not uid:
        return None, Response(
            {'erreur': 'utilisateur_id requis.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        return Utilisateur.objects.get(pk=uid), None
    except Utilisateur.DoesNotExist:
        return None, Response(
            {'erreur': 'Utilisateur introuvable.'},
            status=status.HTTP_404_NOT_FOUND
        )


class ListeVetementsView(APIView):
    def get(self, request):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        vetements = get_vetements_utilisateur(utilisateur)
        return Response(VetementSerializer(vetements, many=True).data)

    def post(self, request):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        serializer = VetementSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        vetement = creer_vetement(
            utilisateur=utilisateur,
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
    def get(self, request, pk):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        vetement = get_vetement_par_id(pk, utilisateur)
        if not vetement:
            return Response({'erreur': 'Vêtement introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(VetementSerializer(vetement).data)

    def put(self, request, pk):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        vetement = get_vetement_par_id(pk, utilisateur)
        if not vetement:
            return Response({'erreur': 'Vêtement introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = VetementSerializer(vetement, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        vetement = modifier_vetement(pk, utilisateur,
                                     **serializer.validated_data)
        return Response(VetementSerializer(vetement).data)

    def patch(self, request, pk):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        vetement = get_vetement_par_id(pk, utilisateur)
        if not vetement:
            return Response({'erreur': 'Vêtement introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        vetement = modifier_vetement(pk, utilisateur, **request.data)
        return Response(VetementSerializer(vetement).data)

    def delete(self, request, pk):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        supprime = supprimer_vetement(pk, utilisateur)
        if not supprime:
            return Response({'erreur': 'Vêtement introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RechercheVetementsView(APIView):
    def get(self, request):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        terme = request.query_params.get('q', '').strip()
        mode  = request.query_params.get('mode', 'baseline')
        if not terme:
            return Response({'erreur': 'Paramètre q requis.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if mode == 'trie':
            resultats = rechercher_vetements_trie(utilisateur, terme)
        else:
            resultats = rechercher_vetements(utilisateur, terme)
        return Response(VetementSerializer(resultats, many=True).data)


class ComparerRechercheView(APIView):
    def get(self, request):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        terme = request.query_params.get('q', '').strip()
        if not terme:
            return Response({'erreur': 'Paramètre q requis.'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(comparer_recherche(utilisateur, terme))


class TriVetementsAVLView(APIView):
    def get(self, request):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        resultats = trier_vetements_avl(utilisateur)
        return Response([
            {'score': score, 'vetement': VetementSerializer(v).data}
            for score, v in resultats
        ])


class MarquerSaleView(APIView):
    def patch(self, request, pk):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        vetement = marquer_sale(pk, utilisateur)
        if not vetement:
            return Response({'erreur': 'Vêtement introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(VetementSerializer(vetement).data)


class MarquerPropreView(APIView):
    def patch(self, request, pk):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        vetement = marquer_propre(pk, utilisateur)
        if not vetement:
            return Response({'erreur': 'Vêtement introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(VetementSerializer(vetement).data)


class SuggererRemplacementView(APIView):
    def get(self, request, pk):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        vetement = get_vetement_par_id(pk, utilisateur)
        if not vetement:
            return Response({'erreur': 'Vêtement introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        remplacement = suggerer_remplacement(vetement, utilisateur)
        if not remplacement:
            return Response({'erreur': 'Aucun remplacement disponible.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(VetementSerializer(remplacement).data)


class StatsGardeRobeView(APIView):
    def get(self, request):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        return Response(stats_garde_robe(utilisateur))


class VetementsPourTenueView(APIView):
    def get(self, request):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        saison = request.query_params.get('saison')
        style  = request.query_params.get('style')
        result = vetements_disponibles_pour_tenue(
            utilisateur, saison=saison, style=style
        )
        return Response({
            'hauts':       VetementSerializer(result['hauts'], many=True).data,
            'bas':         VetementSerializer(result['bas'], many=True).data,
            'accessoires': VetementSerializer(result['accessoires'], many=True).data,
            'suffisant':   result['suffisant'],
        })