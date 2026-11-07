from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django.db import models

from .models import Humeur, Notation
from .serializers import HumeurSerializer, NotationSerializer
from outfits.models import Tenue
from wardrobe.services.sliding_window import marquer_tenue_portee


class HumeurViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les humeurs/sentiments.
    Les utilisateurs ne voient que leurs propres humeurs.
    """
    queryset = Humeur.objects.all()
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    serializer_class = HumeurSerializer

    def get_queryset(self):
        return Humeur.objects.filter(utilisateur=self.request.user)

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)


class NotationViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les notations de tenues.
    Permet aux utilisateurs de noter les tenues et alimente l'apprentissage des préférences.
    Si est_portee=True, la tenue est ajoutée à la fenêtre glissante des vêtements portés.
    """
    queryset = Notation.objects.all()
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    serializer_class = NotationSerializer

    def get_queryset(self):
        return Notation.objects.filter(utilisateur=self.request.user)

    def perform_create(self, serializer):
        notation = serializer.save(utilisateur=self.request.user)
        # Si la tenue est marquée comme portée, on l'ajoute à l'historique sliding window
        if notation.est_portee and notation.tenue:
            marquer_tenue_portee(notation.tenue)

    def perform_update(self, serializer):
        notation = serializer.save()
        if notation.est_portee and notation.tenue:
            marquer_tenue_portee(notation.tenue)
        # Note: si est_portee passe de True à False, on ne retire pas de la window (complexe)

    @action(detail=False, methods=['get'])
    def stats_utilisateur(self, request):
        """GET /api/notations/stats_utilisateur/ — Stats des notations de l'utilisateur"""
        notations = Notation.objects.filter(utilisateur=request.user)
        notes_count = notations.values('note').annotate(count=models.Count('note'))
        moyenne = notations.aggregate(note_moyenne=models.Avg('note'))['note_moyenne'] or 0

        return Response({
            'total_notations': notations.count(),
            'moyenne_notes': round(moyenne, 2),
            'distribution': list(notes_count),
            'tenues_portees': notations.filter(est_portee=True).count(),
        })

    @action(detail=False, methods=['get'])
    def meilleures_tenues(self, request):
        """GET /api/notations/meilleures_tenues/ — Top 5 tenues les mieux notées"""
        top = Notation.objects.filter(utilisateur=request.user).order_by('-note')[:5]
        return Response(NotationSerializer(top, many=True).data)
