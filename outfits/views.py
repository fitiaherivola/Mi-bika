from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication, SessionAuthentication

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
from outfits.services.dijkstra import (
    generer_tenue_dijkstra,
    comparer_dijkstra_vs_baseline,
)
from outfits.services.backtracking import generer_tenue_backtracking
from outfits.services.mlp import recommander_tenues_mlp
from wardrobe.services.sliding_window import get_vetements_recemment_portes
from wardrobe.services.constraints import appliquer_contraintes


class GenererTenueBaselineView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        saison = request.data.get('saison')
        style  = request.data.get('style')
        top_k  = int(request.data.get('top_k', 5))

        # Récupérer les IDs récents à exclure (anti-répétition)
        ids_recents = get_vetements_recemment_portes(request.user, jours=7)

        tenues = generer_et_sauvegarder_baseline(
            utilisateur=request.user,
            saison=saison,
            style=style,
            top_k=top_k,
            ids_exclus=ids_recents,
        )
        if not tenues:
            return Response(
                {'erreur': 'Garde-robe insuffisante.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(TenueSerializer(tenues, many=True).data,
                        status=status.HTTP_201_CREATED)


class GenererTenueOptimiseView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        saison             = request.data.get('saison')
        etat               = request.data.get('etat', request.data.get('humeur', 'neutre'))
        condition_meteo    = request.data.get('condition_meteo')
        saison_actuelle    = request.data.get('saison_actuelle')
        top_k              = int(request.data.get('top_k', 5))

        # 1. Récupérer les IDs récents (anti-répétition)
        ids_recents = get_vetements_recemment_portes(request.user, jours=7)

        # 2. Appliquer les contraintes personnelles actives
        params_gen = appliquer_contraintes(
            utilisateur=request.user,
            saison=saison,
            style=request.data.get('style'),
            avec_accessoire=True
        )
        # Fusion avec params explicites
        styles_autorises = params_gen.get('styles_autorises')
        avec_accessoire   = params_gen.get('avec_accessoire', True)
        ids_exclus        = list(set(ids_recents + params_gen.get('ids_exclus', [])))

        tenues = generer_et_sauvegarder_optimise(
            utilisateur=request.user,
            saison=saison,
            etat=etat,
            condition_meteo=condition_meteo,
            saison_actuelle=saison_actuelle,
            top_k=top_k,
            ids_exclus=ids_exclus,
            styles_autorises=styles_autorises,
            avec_accessoire=avec_accessoire,
        )
        if not tenues:
            return Response(
                {'erreur': 'Garde-robe insuffisante ou aucune tenue trouvée.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(TenueSerializer(tenues, many=True).data,
                        status=status.HTTP_201_CREATED)


class ComparerAlgorithmesView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        resultats = comparer_algorithmes(
            utilisateur=request.user,
            saison=request.data.get('saison'),
            humeur=request.data.get('etat', request.data.get('humeur', 'neutre')),
            condition_meteo=request.data.get('condition_meteo'),
            saison_actuelle=request.data.get('saison_actuelle'),
            top_k=int(request.data.get('top_k', 5))
        )
        return Response(resultats, status=status.HTTP_200_OK)


class RecommandationKNNView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        tenue_id = request.data.get('tenue_id')
        humeur   = request.data.get('humeur')
        k        = int(request.data.get('k', 3))

        if tenue_id:
            try:
                tenue_ref = Tenue.objects.get(
                    id=tenue_id,
                    utilisateur=request.user
                )
            except Tenue.DoesNotExist:
                return Response({'erreur': 'Tenue introuvable.'},
                                status=status.HTTP_404_NOT_FOUND)
            resultats = recommander_tenues_similaires(request.user, tenue_ref, k=k)

        elif humeur:
            resultats = recommander_depuis_humeur(request.user, humeur, k=k)

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


# ═══════════════════════════════════════════════════════════════
# DIJKSTRA — Tenue la plus harmonieuse
# ═══════════════════════════════════════════════════════════════


class GenererTenueDijkstraView(APIView):
    """
    POST /api/outfits/generer/dijkstra/
    Génère la tenue optimale selon l'algorithme de Dijkstra
    (chemin minimal dans le graphe de compatibilité).
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        saison             = request.data.get('saison')
        style              = request.data.get('style')
        avec_accessoire    = request.data.get('avec_accessoire', True)

        result = generer_tenue_dijkstra(
            utilisateur=request.user,
            saison=saison,
            style=style,
            avec_accessoire=avec_accessoire
        )

        if not result:
            return Response(
                {'erreur': 'Garde-robe insuffisante ou aucune combinaison valide.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Sauvegarde la tenue en base
        tenue = Tenue.objects.create(
            utilisateur=request.user,
            haut=result['haut'],
            bas=result['bas'],
            accessoire=result.get('accessoire'),
            score_harmonie=result['score_harmonie'],
            algorithme=result.get('algorithme', 'dijkstra'),
        )
        result['tenue_id'] = tenue.id
        result['tenue']    = TenueSerializer(tenue).data

        return Response(result, status=status.HTTP_201_CREATED)


class ComparerDijkstraView(APIView):
    """
    POST /api/outfits/comparer/dijkstra/
    Compare Dijkstra vs baseline sur le même utilisateur.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        saison = request.data.get('saison')
        resultats = comparer_dijkstra_vs_baseline(
            utilisateur=request.user,
            saison=saison
        )
        return Response(resultats, status=status.HTTP_200_OK)


class GenererTenueBacktrackingView(APIView):
    """
    POST /api/outfits/generer/backtracking/
    Génère une tenue en respectant toutes les contraintes (exploration).
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        saison = request.data.get('saison')
        avec_accessoire = request.data.get('avec_accessoire', False)
        ids_recents = get_vetements_recemment_portes(request.user, jours=7)

        result = generer_tenue_backtracking(
            utilisateur=request.user,
            saison=saison,
            ids_portes_recemment=ids_recents,
            avec_accessoire=avec_accessoire,
        )
        if not result:
            return Response(
                {'erreur': 'Aucune tenue ne satisfait toutes les contraintes.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tenue = Tenue.objects.create(
            utilisateur=request.user,
            haut=result['haut'],
            bas=result['bas'],
            accessoire=result.get('accessoire'),
            score_harmonie=result.get('score_harmonie', 0),
            algorithme=result.get('algorithme', 'backtracking'),
        )
        return Response({
            'tenue': TenueSerializer(tenue).data,
            'algorithme': tenue.algorithme,
            'nb_noeuds': result.get('nb_noeuds', 0),
        }, status=status.HTTP_201_CREATED)


class RecommandationMLPView(APIView):
    """
    POST /api/outfits/recommander/mlp/
    Recommandations via mini réseau de neurones (MLP).
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        top_k = int(request.data.get('top_k', 5))
        resultats = recommander_tenues_mlp(request.user, top_k=top_k)
        if not resultats:
            return Response(
                {'erreur': 'Historique de notations insuffisant pour entraîner le MLP.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response([
            {
                'tenue': TenueSerializer(r['tenue']).data,
                'score_mlp': r['score_mlp'],
                'algorithme': r['algorithme'],
            }
            for r in resultats
        ])


class ListeTenuesView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tenues = Tenue.objects.filter(
            utilisateur=request.user
        ).select_related('haut', 'bas', 'accessoire')
        return Response(TenueSerializer(tenues, many=True).data)


class DetailTenueView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            tenue = Tenue.objects.get(id=pk, utilisateur=request.user)
        except Tenue.DoesNotExist:
            return Response({'erreur': 'Tenue introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(TenueSerializer(tenue).data)

    def delete(self, request, pk):
        try:
            tenue = Tenue.objects.get(id=pk, utilisateur=request.user)
        except Tenue.DoesNotExist:
            return Response({'erreur': 'Tenue introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        tenue.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
