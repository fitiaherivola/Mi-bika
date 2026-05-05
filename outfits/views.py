from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.models import Utilisateur
from outfits.models import Tenue
from outfits.serializers import TenueSerializer
from outfits.services.base import generer_et_sauvegarder_baseline
from outfits.services.optimise import (
    generer_et_sauvegarder_optimise,
    comparer_algorithmes
)
from outfits.services.knn import (
    recommander_tenues_similaires,
    recommander_depuis_humeur,
)


def get_utilisateur(request):
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


class GenererTenueBaselineView(APIView):
    def post(self, request):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        saison = request.data.get('saison')
        style  = request.data.get('style')
        top_k  = int(request.data.get('top_k', 5))

        tenues = generer_et_sauvegarder_baseline(
            utilisateur=utilisateur,
            saison=saison,
            style=style,
            top_k=top_k
        )
        if not tenues:
            return Response(
                {'erreur': 'Garde-robe insuffisante.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(TenueSerializer(tenues, many=True).data,
                        status=status.HTTP_201_CREATED)


class GenererTenueOptimiseView(APIView):
    def post(self, request):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        saison          = request.data.get('saison')
        style           = request.data.get('style')
        humeur          = request.data.get('humeur', 'neutre')
        condition_meteo = request.data.get('condition_meteo')
        saison_actuelle = request.data.get('saison_actuelle')
        top_k           = int(request.data.get('top_k', 5))

        tenues = generer_et_sauvegarder_optimise(
            utilisateur=utilisateur,
            saison=saison,
            style=style,
            humeur=humeur,
            condition_meteo=condition_meteo,
            saison_actuelle=saison_actuelle,
            top_k=top_k
        )
        if not tenues:
            return Response(
                {'erreur': 'Garde-robe insuffisante ou aucune tenue trouvée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(TenueSerializer(tenues, many=True).data,
                        status=status.HTTP_201_CREATED)


class ComparerAlgorithmesView(APIView):
    def post(self, request):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        resultats = comparer_algorithmes(
            utilisateur=utilisateur,
            saison=request.data.get('saison'),
            humeur=request.data.get('humeur', 'neutre'),
            condition_meteo=request.data.get('condition_meteo'),
            saison_actuelle=request.data.get('saison_actuelle'),
            top_k=int(request.data.get('top_k', 5))
        )
        return Response(resultats, status=status.HTTP_200_OK)


class RecommandationKNNView(APIView):
    def post(self, request):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        tenue_id = request.data.get('tenue_id')
        humeur   = request.data.get('humeur')
        k        = int(request.data.get('k', 3))

        if tenue_id:
            try:
                tenue_ref = Tenue.objects.get(
                    id=tenue_id,
                    utilisateur=utilisateur
                )
            except Tenue.DoesNotExist:
                return Response({'erreur': 'Tenue introuvable.'},
                                status=status.HTTP_404_NOT_FOUND)
            resultats = recommander_tenues_similaires(utilisateur, tenue_ref, k=k)

        elif humeur:
            resultats = recommander_depuis_humeur(utilisateur, humeur, k=k)

        else:
            return Response({'erreur': 'Fournissez tenue_id ou humeur.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if not resultats:
            return Response({'erreur': 'Historique insuffisant pour le k-NN.'},
                            status=status.HTTP_404_NOT_FOUND)

        return Response([
            {
                'tenue':      TenueSerializer(r['tenue']).data,
                'similarite': r['similarite'],
                'distance':   r['distance'],
            }
            for r in resultats
        ], status=status.HTTP_200_OK)


class ListeTenuesView(APIView):
    def get(self, request):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        tenues = Tenue.objects.filter(
            utilisateur=utilisateur
        ).select_related('haut', 'bas', 'accessoire')
        return Response(TenueSerializer(tenues, many=True).data)


class DetailTenueView(APIView):
    def get(self, request, pk):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        try:
            tenue = Tenue.objects.get(id=pk, utilisateur=utilisateur)
        except Tenue.DoesNotExist:
            return Response({'erreur': 'Tenue introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(TenueSerializer(tenue).data)

    def delete(self, request, pk):
        utilisateur, err = get_utilisateur(request)
        if err:
            return err
        try:
            tenue = Tenue.objects.get(id=pk, utilisateur=utilisateur)
        except Tenue.DoesNotExist:
            return Response({'erreur': 'Tenue introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        tenue.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)