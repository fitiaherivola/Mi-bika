"""
Notifications push Firebase Cloud Messaging (BF9).
Configurez FCM_SERVER_KEY dans .env pour activer l'envoi réel.
"""
import json

import requests
from django.conf import settings


def envoyer_push(utilisateur, titre, corps, data=None):
    """
    Envoie une notification push si FCM_SERVER_KEY est configurée.
    En prototype, enregistre seulement en log si pas de device token.
    """
    key = getattr(settings, 'FCM_SERVER_KEY', '')
    if not key:
        return False

    # Nécessite un device_token stocké sur le profil utilisateur (extension future)
    device_token = getattr(utilisateur, 'fcm_device_token', None)
    if not device_token:
        return False

    payload = {
        'to': device_token,
        'notification': {'title': titre, 'body': corps},
        'data': data or {},
    }
    try:
        r = requests.post(
            'https://fcm.googleapis.com/fcm/send',
            headers={
                'Authorization': f'key={key}',
                'Content-Type': 'application/json',
            },
            data=json.dumps(payload),
            timeout=10,
        )
        return r.status_code == 200
    except requests.RequestException:
        return False
