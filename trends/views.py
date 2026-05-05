from rest_framework import viewsets
from .models import Tendance
from .serializers import TendanceSerializer


class TendanceViewSet(viewsets.ModelViewSet):
    """ViewSet pour les tendances de mode."""
    queryset = Tendance.objects.all()
    serializer_class = TendanceSerializer
    filterset_fields = ['popularite']
    search_fields = ['titre']
