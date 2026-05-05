from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from weather.models import Meteo
from weather.serializers import MeteoSerializer
from weather.services.base import (
    get_meteo_du_jour,
    get_meteo_par_ville,
    enregistrer_meteo,
    contraintes_depuis_ville,
    stats_meteo,
)


class MeteoduJourView(APIView):
    """
    GET /api/meteo/aujourd-hui/?ville=Antananarivo
    Retourne la météo du jour pour une ville.
    """
    def get(self, request):
        ville = request.query_params.get('ville', 'Antananarivo')
        meteo = get_meteo_du_jour(ville)

        if not meteo:
            return Response(
                {'erreur': f"Aucune météo disponible pour {ville} aujourd'hui."},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(MeteoSerializer(meteo).data)


class HistoriqueMeteoView(APIView):
    """
    GET /api/meteo/historique/?ville=Antananarivo&jours=7
    Retourne l'historique météo d'une ville.
    """
    def get(self, request):
        ville = request.query_params.get('ville', 'Antananarivo')
        jours = int(request.query_params.get('jours', 7))

        historique = get_meteo_par_ville(ville, jours)

        if not historique:
            return Response(
                {'erreur': f"Aucun historique pour {ville}."},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(MeteoSerializer(historique, many=True).data)


class EnregistrerMeteoView(APIView):
    """
    POST /api/meteo/enregistrer/
    Enregistre une nouvelle météo pour une ville.

    Body :
        {
            "ville"           : "Antananarivo",
            "temperature"     : 22.5,
            "condition"       : "ensoleille",
            "date_prediction" : "2026-05-03"  (optionnel)
        }
    """
    def post(self, request):
        serializer = MeteoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

        meteo = enregistrer_meteo(
            ville=serializer.validated_data['ville'],
            temperature=serializer.validated_data['temperature'],
            condition=serializer.validated_data['condition'],
            date_prediction=serializer.validated_data.get('date_prediction'),
        )
        return Response(MeteoSerializer(meteo).data,
                        status=status.HTTP_201_CREATED)


class ContraintesMeteoView(APIView):
    """
    GET /api/meteo/contraintes/?ville=Antananarivo
    Convertit la météo du jour en contraintes pour la génération de tenues.
    C'est le pont entre weather et outfits.
    """
    def get(self, request):
        ville = request.query_params.get('ville', 'Antananarivo')
        contraintes = contraintes_depuis_ville(ville)

        if not contraintes:
            return Response(
                {'erreur': f"Météo introuvable pour {ville}."},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response({
            'ville':           ville,
            'condition_meteo': contraintes['condition_meteo'],
            'saison_actuelle': contraintes['saison_actuelle'],
            'temperature':     contraintes['temperature'],
            'conseil':         contraintes['conseil'],
        })


class StatsMeteoView(APIView):
    """
    GET /api/meteo/stats/?ville=Antananarivo&jours=7
    Statistiques météo sur N jours — utile pour la démo.
    """
    def get(self, request):
        ville = request.query_params.get('ville', 'Antananarivo')
        jours = int(request.query_params.get('jours', 7))
        stats = stats_meteo(ville, jours)
        return Response(stats)