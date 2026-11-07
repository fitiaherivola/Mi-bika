from rest_framework import viewsets, permissions, status
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Tendance, Boutique
from .serializers import TendanceSerializer, BoutiqueSerializer
from .services.base import (
    get_tendances_pour_utilisateur,
    get_tendances_similaires,
    enrichir_images_boutiques,
)
from .services.external_api import dashboard_external_meta


class TendanceViewSet(viewsets.ModelViewSet):
    """ViewSet pour les tendances de mode."""
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    queryset = Tendance.objects.all()
    serializer_class = TendanceSerializer

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """
        GET /api/trends/tendances/dashboard/
        Tableau de bord tendances personnalisé (BF10).
        """
        tendances = get_tendances_pour_utilisateur(request.user)
        similaires = get_tendances_similaires(request.user, top_k=5)
        meta = dashboard_external_meta(request.user, tendances)
        return Response({
            **meta,
            'tendances_style': tendances,
            'tendances': tendances,
            'top_populaires': similaires,
        })


class DashboardTendancesView(APIView):
    """GET /api/trends/dashboard/ — alias tableau de bord."""
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tendances = get_tendances_pour_utilisateur(request.user)
        meta = dashboard_external_meta(request.user, tendances)
        return Response({
            'tendances': tendances,
            **meta,
        })


class BoutiqueViewSet(viewsets.ModelViewSet):
    """
    API pour les boutiques et créateurs (Crowdsourcée).
    Retourne les boutiques, triées en priorité par le style préféré de l'utilisateur.
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    queryset = Boutique.objects.all()
    serializer_class = BoutiqueSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        user_style = self.request.user.style_prefere
        
        if user_style:
            # Trie d'abord par style_dominant correspondant, puis par popularité
            from django.db.models import Case, When, Value, IntegerField
            qs = qs.annotate(
                is_preferred=Case(
                    When(style_dominant=user_style, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ).order_by('-is_preferred', '-popularite')
        else:
            qs = qs.order_by('-popularite')

        return qs

    def list(self, request, *args, **kwargs):
        boutiques = list(self.filter_queryset(self.get_queryset()))
        enrichir_images_boutiques(boutiques)
        serializer = self.get_serializer(boutiques, many=True)
        return Response(serializer.data)
