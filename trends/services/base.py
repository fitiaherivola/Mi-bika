from trends.models import Tendance
from users.models import Utilisateur
from trends.services.external_api import get_external_tendances, dashboard_external_meta


# Images stables par style (picsum avec seed déterministe)
STYLE_IMAGE_URLS = {
    'CASUAL':       'https://picsum.photos/seed/mibika-casual/400/500',
    'FORMEL':       'https://picsum.photos/seed/mibika-formel/400/500',
    'SPORT':        'https://picsum.photos/seed/mibika-sport/400/500',
    'TRADITIONNEL': 'https://picsum.photos/seed/mibika-traditionnel/400/500',
    'SOIREE':       'https://picsum.photos/seed/mibika-soiree/400/500',
}


def get_image_tendance(style: str) -> str:
    """Retourne une URL d'illustration selon le style (API tendances)."""
    return STYLE_IMAGE_URLS.get(style, 'https://picsum.photos/seed/mibika-mode/400/500')


def enrichir_images_boutiques(boutiques: list) -> list:
    for b in boutiques:
        if not b.image_url and b.style_dominant:
            b.image_url = get_image_tendance(b.style_dominant)
    return boutiques


def enrichir_images_tendances(tendances: list, style_fallback=None) -> list:
    """Ajoute image_url depuis l'API tendances si absente en base."""
    for t in tendances:
        if not t.image_url:
            t.image_url = get_image_tendance(t.style or style_fallback or 'CASUAL')
    return tendances


def get_tendances_pour_utilisateur(utilisateur: Utilisateur) -> list:
    """Produits mode uniquement via APIs externes, style utilisateur en priorité."""
    return get_external_tendances(utilisateur, limit=24)


def get_tendances_similaires(utilisateur: Utilisateur, top_k: int = 5) -> list:
    """Top-k produits API externes pour le style de l'utilisateur."""
    items = get_external_tendances(utilisateur, limit=top_k * 3)
    return [i for i in items if i.get('match_style')][:top_k] or items[:top_k]