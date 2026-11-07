from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from weather.services.base import (
    get_meteo_du_jour,
    get_derniere_meteo,
    get_meteo_par_ville,
    enregistrer_meteo,
    contraintes_depuis_ville,
    stats_meteo,
    meteo_fallback_dict,
)
from weather.services.openmeteo import sync_weather_for_city
from weather.serializers import MeteoSerializer


def _serialize_meteo(meteo, source: str, stale: bool = False):
    data = MeteoSerializer(meteo).data
    data['source'] = source
    if stale:
        data['stale'] = True
    return data


class MeteoduJourView(APIView):
    """
    GET /api/weather/aujourd-hui/?ville=Antananarivo
    Réponse rapide : base locale d'abord, jamais de blocage API sur le GET.
    ?sync=1 pour forcer un appel Open-Meteo.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        ville = request.query_params.get('ville', 'Antananarivo')
        force_sync = request.query_params.get('sync', '').lower() in ('1', 'true', 'yes')

        meteo = get_meteo_du_jour(ville)
        if meteo:
            return Response(_serialize_meteo(meteo, 'db'))

        # Dernière météo en cache (autre jour) — affichage immédiat
        derniere = get_derniere_meteo(ville)
        if derniere and not force_sync:
            return Response(_serialize_meteo(derniere, 'cache', stale=True))

        # Sync externe uniquement si demandé explicitement (bouton Sync)
        if force_sync:
            sync_weather_for_city(ville)
            meteo = get_meteo_du_jour(ville) or get_derniere_meteo(ville)
            if meteo:
                return Response(_serialize_meteo(meteo, 'open-meteo'))

        if derniere:
            return Response(_serialize_meteo(derniere, 'cache', stale=True))

        return Response(meteo_fallback_dict(ville))


class SyncWeatherView(APIView):
    """
    POST /api/weather/sync/
    Déclenche une synchronisation manuelle avec Open-Meteo.
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def post(self, request):
        ville = request.data.get('ville') or request.query_params.get('ville', 'Antananarivo')
        success = sync_weather_for_city(ville)

        if success:
            meteo = get_meteo_du_jour(ville) or get_derniere_meteo(ville)
            return Response({
                'message': f'Météo synchronisée pour {ville}',
                'meteo': MeteoSerializer(meteo).data if meteo else None,
            }, status=status.HTTP_200_OK)
        meteo = get_derniere_meteo(ville)
        if meteo:
            return Response({
                'message': 'API externe indisponible — dernières données en cache',
                'meteo': MeteoSerializer(meteo).data,
                'stale': True,
            }, status=status.HTTP_200_OK)
        return Response({
            'erreur': 'Échec sync Open-Meteo. Réessayez dans un instant.',
            'meteo': meteo_fallback_dict(ville),
        }, status=status.HTTP_200_OK)


class HistoriqueMeteoView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        ville = request.query_params.get('ville', 'Antananarivo')
        jours = int(request.query_params.get('jours', 7))
        historique = get_meteo_par_ville(ville, jours)
        if not historique:
            return Response(
                {'erreur': f"Aucun historique pour {ville}."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(MeteoSerializer(historique, many=True).data)


class EnregistrerMeteoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MeteoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        meteo = enregistrer_meteo(
            ville=serializer.validated_data['ville'],
            temperature=serializer.validated_data['temperature'],
            condition=serializer.validated_data['condition'],
            date_prediction=serializer.validated_data.get('date_prediction'),
        )
        return Response(MeteoSerializer(meteo).data, status=status.HTTP_201_CREATED)


class ContraintesMeteoView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        ville = request.query_params.get('ville', 'Antananarivo')
        contraintes = contraintes_depuis_ville(ville)
        if not contraintes:
            return Response(
                {'erreur': f"Météo introuvable pour {ville}."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({
            'ville': ville,
            'condition_meteo': contraintes['condition_meteo'],
            'saison_actuelle': contraintes['saison_actuelle'],
            'temperature': contraintes['temperature'],
            'conseil': contraintes['conseil'],
        })


class StatsMeteoView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        ville = request.query_params.get('ville', 'Antananarivo')
        jours = int(request.query_params.get('jours', 7))
        return Response(stats_meteo(ville, jours))
