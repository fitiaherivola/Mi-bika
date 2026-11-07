from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from users.models import Utilisateur
from users.jwt_utils import decode_token


class JWTAuthentication(BaseAuthentication):
    """
    Authentification Bearer JWT.
    Header: Authorization: Bearer <jwt_access>
    """

    keyword = 'Bearer'

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith(f'{self.keyword} '):
            return None

        token = auth_header[len(self.keyword) + 1:].strip()
        payload = decode_token(token)
        if not payload:
            raise AuthenticationFailed('Token JWT invalide ou expiré.')

        if payload.get('type') == 'refresh':
            raise AuthenticationFailed('Utilisez un token access, pas refresh.')

        try:
            user = Utilisateur.objects.get(pk=payload['user_id'])
        except Utilisateur.DoesNotExist:
            raise AuthenticationFailed('Utilisateur introuvable.')

        if not user.is_active:
            raise AuthenticationFailed('Compte désactivé.')

        return (user, token)
