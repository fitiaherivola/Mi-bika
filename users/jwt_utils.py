"""
JWT (JSON Web Tokens) pour l'authentification Mi-bika.
Conforme au cahier des charges : tokens sécurisés pour web/mobile.
"""
import jwt
from datetime import datetime, timedelta, timezone

from django.conf import settings


def _now():
    return datetime.now(timezone.utc)


def create_access_token(user) -> str:
    payload = {
        'user_id': user.id,
        'username': user.username,
        'type': 'access',
        'exp': _now() + timedelta(minutes=getattr(settings, 'JWT_ACCESS_MINUTES', 60)),
        'iat': _now(),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


def create_refresh_token(user) -> str:
    payload = {
        'user_id': user.id,
        'type': 'refresh',
        'exp': _now() + timedelta(days=getattr(settings, 'JWT_REFRESH_DAYS', 7)),
        'iat': _now(),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
    except jwt.PyJWTError:
        return None


def get_user_id_from_token(token: str) -> int | None:
    payload = decode_token(token)
    if not payload:
        return None
    return payload.get('user_id')
