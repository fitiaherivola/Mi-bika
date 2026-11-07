"""
Récupération de produits mode via APIs externes (DummyJSON + Fake Store).

Priorisation : le style préféré de l'utilisateur est toujours en tête.
"""

import json
import time
import urllib.error
import urllib.request
from typing import Optional
from urllib.parse import quote

from users.models import Utilisateur

USD_TO_MGA = 4500
CACHE_TTL_SEC = 3600

_cache: dict = {'items': [], 'fetched_at': 0.0}

DUMMYJSON_CATEGORIES = [
    'mens-shirts',
    'womens-dresses',
    'tops',
    'mens-shoes',
    'womens-shoes',
    'womens-bags',
    'sunglasses',
    'womens-jewellery',
]

FAKESTORE_CATEGORIES = ["men's clothing", "women's clothing", "jewelery"]

STYLE_KEYWORDS = {
    'SPORT': [
        'sport', 'running', 'gym', 'sneaker', 'athletic', 'train', 'fitness',
        'jogging', 'performance',
    ],
    'FORMEL': [
        'formal', 'suit', 'blazer', 'business', 'dress shirt', 'office',
        'professional', 'tie', 'watch', 'gown',
    ],
    'SOIREE': [
        'evening', 'cocktail', 'party', 'gown', 'lace', 'silk', 'elegant',
        'sequin', 'glamour',
    ],
    'TRADITIONNEL': [
        'traditional', 'ethnic', 'cultural', 'heritage', 'lamba', 'woven',
    ],
    'STREETWEAR': ['street', 'urban', 'hoodie', 'oversize', 'skate'],
    'CHIC': ['chic', 'luxury', 'designer', 'leather', 'premium', 'couture'],
    'BOHEME': ['boho', 'bohemian', 'flowy', 'floral', 'crochet'],
    'RETRO': ['vintage', 'retro', 'classic', 'old-school'],
    'GRUNGE': ['grunge', 'ripped', 'distressed', 'punk'],
    'CASUAL': [
        'casual', 'tshirt', 't-shirt', 'shirt', 'jean', 'plaid', 'cotton',
        'everyday', 'dress', 'frock', 'top', 'bag',
    ],
}


def _http_get_json(url: str, timeout: int = 12) -> Optional[dict | list]:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mi-bika/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, TimeoutError):
        return None


def detect_style(title: str, description: str = '', category: str = '') -> str:
    """Détecte le style Mi-bika le plus probable à partir du texte produit."""
    text = f'{title} {description} {category}'.lower()
    cat = category.lower()

    if any(k in cat for k in ('shoe', 'sneaker', 'sport')):
        return 'SPORT'
    if any(k in cat for k in ('dress', 'gown', 'evening')):
        return 'SOIREE'
    if 'watch' in cat or 'jewel' in cat:
        return 'CHIC'
    if 'shirt' in cat:
        return 'CASUAL'

    scores = {style: 0 for style in STYLE_KEYWORDS}
    for style, keywords in STYLE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[style] += 1
    best_style = max(scores, key=scores.get)
    return best_style if scores[best_style] > 0 else 'CASUAL'


def _format_prix_ar(amount_mga: int) -> str:
    return f'{amount_mga:,}'.replace(',', ' ') + ' Ar'


def _normalize_dummyjson(product: dict) -> dict:
    price_usd = float(product.get('price') or 0)
    prix_ar = int(round(price_usd * USD_TO_MGA))
    style = detect_style(
        product.get('title', ''),
        product.get('description', ''),
        product.get('category', ''),
    )
    rating = float(product.get('rating') or 0)
    images = product.get('images') or []
    image_url = product.get('thumbnail') or (images[0] if images else '')

    return {
        'id': f'dj-{product["id"]}',
        'titre': product.get('title', 'Article mode'),
        'description': (product.get('description') or '')[:220],
        'style': style,
        'popularite': int(rating * 20),
        'rating': rating,
        'image_url': image_url,
        'prix_usd': round(price_usd, 2),
        'prix_ar': prix_ar,
        'prix_affichage': _format_prix_ar(prix_ar),
        'source': 'dummyjson',
        'categorie': product.get('category', ''),
        'lien_produit': f"https://dummyjson.com/products/{product['id']}",
    }


def _normalize_fakestore(product: dict) -> dict:
    price_usd = float(product.get('price') or 0)
    prix_ar = int(round(price_usd * USD_TO_MGA))
    style = detect_style(
        product.get('title', ''),
        product.get('description', ''),
        product.get('category', ''),
    )
    rating = product.get('rating', {})
    rate = float(rating.get('rate', 0) if isinstance(rating, dict) else 0)
    count = int(rating.get('count', 0) if isinstance(rating, dict) else 0)

    return {
        'id': f'fs-{product["id"]}',
        'titre': product.get('title', 'Article mode'),
        'description': (product.get('description') or '')[:220],
        'style': style,
        'popularite': count or int(rate * 20),
        'rating': rate,
        'image_url': product.get('image', ''),
        'prix_usd': round(price_usd, 2),
        'prix_ar': prix_ar,
        'prix_affichage': _format_prix_ar(prix_ar),
        'source': 'fakestoreapi',
        'categorie': product.get('category', ''),
        'lien_produit': None,
    }


def fetch_external_products(force_refresh: bool = False) -> list[dict]:
    """Charge les produits depuis les APIs externes (avec cache mémoire)."""
    now = time.time()
    if not force_refresh and _cache['items'] and (now - _cache['fetched_at']) < CACHE_TTL_SEC:
        return list(_cache['items'])

    items: list[dict] = []
    seen_titles: set[str] = set()

    for cat in DUMMYJSON_CATEGORIES:
        data = _http_get_json(f'https://dummyjson.com/products/category/{cat}?limit=8')
        if not data:
            continue
        for p in data.get('products', []):
            title_key = (p.get('title') or '').strip().lower()
            if not title_key or title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            items.append(_normalize_dummyjson(p))

    for cat in FAKESTORE_CATEGORIES:
        url = f'https://fakestoreapi.com/products/category/{quote(cat, safe="")}'
        data = _http_get_json(url)
        if not data or not isinstance(data, list):
            continue
        for p in data:
            title_key = (p.get('title') or '').strip().lower()
            if not title_key or title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            items.append(_normalize_fakestore(p))

    _cache['items'] = items
    _cache['fetched_at'] = now
    return list(items)


def prioritize_by_user_style(products: list[dict], user_style: Optional[str]) -> list[dict]:
    """
    Trie les produits : style utilisateur en premier, puis popularité/note.
    """
    style = user_style or 'CASUAL'

    for p in products:
        p['match_style'] = p.get('style') == style

    return sorted(
        products,
        key=lambda p: (
            -int(p.get('match_style', False)),
            -int(p.get('popularite', 0)),
            -float(p.get('rating', 0)),
        ),
    )


def get_external_tendances(utilisateur: Utilisateur, limit: int = 24) -> list[dict]:
    """Produits externes priorisés selon le style de l'utilisateur."""
    products = fetch_external_products()
    prioritized = prioritize_by_user_style(products, utilisateur.style_prefere)
    return prioritized[:limit]


def dashboard_external_meta(utilisateur: Utilisateur, items: list[dict]) -> dict:
    style = utilisateur.style_prefere or 'CASUAL'
    matched = sum(1 for i in items if i.get('match_style'))
    return {
        'filtre_style': style,
        'style_utilisateur': style,
        'total': len(items),
        'total_style_match': matched,
        'sources': ['dummyjson', 'fakestoreapi'],
        'api_externe': True,
    }
