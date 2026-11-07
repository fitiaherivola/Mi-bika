from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate

from users.jwt_utils import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from .models import Utilisateur
from .serializers import UtilisateurSerializer, CreateUtilisateurSerializer


class CreerUtilisateurView(APIView):
    """
    POST /api/users/
    Crée un nouvel utilisateur.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

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
    GET  /api/users/ — Liste tous les utilisateurs (pour admin/ demo)
    POST /api/users/ — Crée un nouvel utilisateur
    Note: En production, cette liste devrait être réservée aux administrateurs.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        # Pour un prototype, on retourne tous les utilisateurs.
        # En production: restreindre aux admin.
        users = Utilisateur.objects.all()
        return Response(UtilisateurSerializer(users, many=True).data)

    def post(self, request):
        serializer = CreateUtilisateurSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        return Response(UtilisateurSerializer(user).data,
                        status=status.HTTP_201_CREATED)


class ProfilView(APIView):
    """
    GET   /api/users/<id>/ → détail utilisateur
    PATCH /api/users/<id>/ → modifier profil
    Note: L'utilisateur ne peut modifier que son propre profil.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get(self, request, pk):
        try:
            user = Utilisateur.objects.get(pk=pk)
        except Utilisateur.DoesNotExist:
            return Response({'erreur': 'Utilisateur introuvable.'},
                            status=status.HTTP_404_NOT_FOUND)
        return Response(UtilisateurSerializer(user).data)

    def patch(self, request, pk):
        # Vérifier que l'utilisateur modifie son propre profil
        if int(pk) != request.user.id:
            return Response(
                {'erreur': 'Vous ne pouvez modifier que votre propre profil.'},
                status=status.HTTP_403_FORBIDDEN
            )
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


class LoginView(APIView):
    """
    POST /api/users/login/
    Authentifie un utilisateur et retourne son token.
    Body: {"username": "...", "password": "..."}
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'erreur': 'Username et password requis.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {'erreur': 'Identifiants invalides.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'jwt_access': create_access_token(user),
            'jwt_refresh': create_refresh_token(user),
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
        }, status=status.HTTP_200_OK)


class JWTRefreshView(APIView):
    """
    POST /api/users/jwt/refresh/
    Body: {"refresh": "<jwt_refresh>"}
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        refresh = request.data.get('refresh')
        if not refresh:
            return Response(
                {'erreur': 'Token refresh requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        payload = decode_token(refresh)
        if not payload or payload.get('type') != 'refresh':
            return Response(
                {'erreur': 'Refresh token invalide.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            user = Utilisateur.objects.get(pk=payload['user_id'])
        except Utilisateur.DoesNotExist:
            return Response(
                {'erreur': 'Utilisateur introuvable.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response({
            'jwt_access': create_access_token(user),
            'jwt_refresh': create_refresh_token(user),
        })


class LogoutView(APIView):
    """
    POST /api/users/logout/
    Déconnecte l'utilisateur en supprimant son token.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def post(self, request):
        try:
            request.user.auth_token.delete()
        except Exception:
            pass
        return Response(
            {'message': 'Déconnexion réussie.'},
            status=status.HTTP_200_OK
        )


class ProfilUtilisateurActuelView(APIView):
    """
    GET /api/users/me/
    Récupère le profil de l'utilisateur authentifié.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UtilisateurSerializer(request.user).data)
