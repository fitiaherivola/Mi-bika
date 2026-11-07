from django.shortcuts import render
from django.views.decorators.http import require_GET

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.authentication import TokenAuthentication, SessionAuthentication

from users.authentication import JWTAuthentication
from wardrobe.models import Vetement
from wardrobe.serializers import VetementSerializer
from wardrobe.services.constraints import get_contraintes_actives
from events.models import Notification
from events.serializers import NotificationSerializer
from weather.services.base import get_meteo_du_jour
from weather.serializers import MeteoSerializer


@require_GET
def home(request):
    """Page d'accueil web Mi-bika (BF13 + BNF4)."""
    return render(request, 'home.html')


class OfflineSyncView(APIView):
    """
    GET /api/sync/offline/
    Paquet de données pour le mode hors-ligne (BNF2).
    Le client mobile/web peut mettre en cache cette réponse.
    """
    authentication_classes = [
        JWTAuthentication,
        TokenAuthentication,
        SessionAuthentication,
    ]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.utils import timezone

        user = request.user
        ville = request.query_params.get('ville', 'Antananarivo')

        vetements = Vetement.objects.filter(utilisateur=user)
        contraintes = get_contraintes_actives(user)
        meteo = get_meteo_du_jour(ville)
        notifs = Notification.objects.filter(
            utilisateur=user, est_lue=False
        ).order_by('-date_envoi')[:20]

        return Response({
            'version': 1,
            'synced_at': timezone.now().isoformat(),
            'utilisateur': {
                'id': user.id,
                'username': user.username,
                'style_prefere': user.style_prefere,
            },
            'wardrobe': VetementSerializer(vetements, many=True).data,
            'contraintes_actives': [
                {
                    'type': c.type_contrainte,
                    'priorite': c.priorite,
                    'label': c.get_type_contrainte_display(),
                }
                for c in contraintes
            ],
            'meteo': MeteoSerializer(meteo).data if meteo else None,
            'notifications': NotificationSerializer(notifs, many=True).data,
            'endpoints': {
                'wardrobe': '/api/wardrobe/',
                'outfits_baseline': '/api/outfits/generer/baseline/',
                'outfits_optimise': '/api/outfits/generer/optimise/',
            },
        })
