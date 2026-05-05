from rest_framework import viewsets
from .models import Humeur
from .serializers import HumeurSerializer


class HumeurViewSet(viewsets.ModelViewSet):
    """ViewSet pour les humeurs/sentiments."""
    queryset = Humeur.objects.all()
    serializer_class = HumeurSerializer
    filterset_fields = ['utilisateur', 'type_humeur']
    search_fields = ['utilisateur__pseudo']
