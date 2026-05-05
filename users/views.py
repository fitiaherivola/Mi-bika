from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .models import Utilisateur
from .serializers import UtilisateurSerializer, CreateUtilisateurSerializer


class CreerUtilisateurView(APIView):
    """
    POST /api/users/
    Crée un nouvel utilisateur.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CreateUtilisateurSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        return Response(UtilisateurSerializer(user).data,
                        status=status.HTTP_201_CREATED)


class ListeUtilisateursView(APIView):
    """
    GET /api/users/
    Liste tous les utilisateurs.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        users = Utilisateur.objects.all()
        return Response(UtilisateurSerializer(users, many=True).data)


class ProfilView(APIView):
    """
    GET   /api/users/<id>/ → détail utilisateur
    PATCH /api/users/<id>/ → modifier profil
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            user = Utilisateur.objects.get(pk=pk)
        except Utilisateur.DoesNotExist:
            return Response({'erreur': 'Utilisateur introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(UtilisateurSerializer(user).data)

    def patch(self, request, pk):
        try:
            user = Utilisateur.objects.get(pk=pk)
        except Utilisateur.DoesNotExist:
            return Response({'erreur': 'Utilisateur introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = UtilisateurSerializer(user, data=request.data,
                                           partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)