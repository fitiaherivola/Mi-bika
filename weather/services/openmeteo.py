"""
Service météo Open-Meteo (open-source).

Aucune clé API requise (usage personnel / non commercial).
Jusqu'à 10 000 requêtes / jour. Données issues des modèles nationaux
(NOAA, DWD, Météo-France, etc.).

APIs utilisées :
  - Geocoding : https://geocoding-api.open-meteo.com/v1/search
  - Forecast  : https://api.open-meteo.com/v1/forecast  (actuel + horaire)
"""

import requests
from datetime import date
from django.conf import settings
from weather.services.base import enregistrer_meteo


OPENMETEO_FORECAST_URL = getattr(
    settings, 'OPENMETEO_FORECAST_URL', 'https://api.open-meteo.com/v1/forecast'
)
OPENMETEO_GEOCODING_URL = getattr(
    settings, 'OPENMETEO_GEOCODING_URL', 'https://geocoding-api.open-meteo.com/v1/search'
)

# Coordonnées connues (évite un appel geocoding pour les villes principales)
VILLES_COORDS = {
    'antananarivo': (-18.8792, 47.5079, 'Antananarivo'),
    'tananarive':   (-18.8792, 47.5079, 'Antananarivo'),
    'toamasina':    (-18.1492, 49.4023, 'Toamasina'),
    'tamatave':     (-18.1492, 49.4023, 'Toamasina'),
    'antsirabe':    (-19.8659, 47.0333, 'Antsirabe'),
    'mahajanga':    (-15.7167, 46.3167, 'Mahajanga'),
    'fianarantsoa': (-21.4536, 47.0854, 'Fianarantsoa'),
    'toliara':      (-23.3500, 43.6667, 'Toliara'),
    'tuléar':       (-23.3500, 43.6667, 'Toliara'),
    'antsiranana':  (-12.2787, 49.2917, 'Antsiranana'),
    'diego':        (-12.2787, 49.2917, 'Antsiranana'),
}

# Codes WMO Open-Meteo → condition Mi-bika
WMO_VERS_CONDITION = {
    0: 'ensoleille',
    1: 'ensoleille',
    2: 'nuageux',
    3: 'nuageux',
    45: 'nuageux',
    48: 'nuageux',
    51: 'pluvieux',
    53: 'pluvieux',
    55: 'pluvieux',
    56: 'pluvieux',
    57: 'pluvieux',
    61: 'pluvieux',
    63: 'pluvieux',
    65: 'pluvieux',
    66: 'pluvieux',
    67: 'pluvieux',
    71: 'froid',
    73: 'froid',
    75: 'froid',
    77: 'froid',
    80: 'pluvieux',
    81: 'pluvieux',
    82: 'pluvieux',
    85: 'froid',
    86: 'froid',
    95: 'pluvieux',
    96: 'pluvieux',
    99: 'pluvieux',
}

_geocode_cache: dict[str, tuple[float, float, str]] = {}


def _normaliser_condition(weather_code: int, temperature: float) -> str:
    """Mappe un code WMO + température vers les valeurs du modèle Meteo."""
    base = WMO_VERS_CONDITION.get(int(weather_code), 'nuageux')
    if temperature >= 30:
        return 'chaud'
    if temperature <= 10:
        return 'froid'
    return base


def geocode_ville(ville: str, country_code: str = 'MG') -> tuple[float, float, str] | None:
    """
    Retourne (latitude, longitude, nom_officiel) pour une ville.
    Cache mémoire + table locale Madagascar, puis API geocoding Open-Meteo.
    """
    key = (ville or '').strip().lower()
    if not key:
        return None
    if key in VILLES_COORDS:
        return VILLES_COORDS[key]
    if key in _geocode_cache:
        return _geocode_cache[key]

    try:
        response = requests.get(
            OPENMETEO_GEOCODING_URL,
            params={
                'name': ville,
                'count': 1,
                'language': 'fr',
                'format': 'json',
                'country': country_code,
            },
            timeout=6,
        )
        response.raise_for_status()
        results = response.json().get('results') or []
        if not results:
            # Retry sans filtre pays si rien trouvé (ex. ville hors MG)
            response = requests.get(
                OPENMETEO_GEOCODING_URL,
                params={
                    'name': ville,
                    'count': 1,
                    'language': 'fr',
                    'format': 'json',
                },
                timeout=6,
            )
            response.raise_for_status()
            results = response.json().get('results') or []
        if not results:
            return None
        hit = results[0]
        coords = (float(hit['latitude']), float(hit['longitude']), hit.get('name') or ville)
        _geocode_cache[key] = coords
        return coords
    except (requests.RequestException, KeyError, ValueError, TypeError):
        return None


def fetch_weather_from_api(ville: str = 'Antananarivo', country_code: str = 'MG') -> dict | None:
    """
    Appelle Open-Meteo (actuel + prévisions horaires) pour une ville.

    Returns:
        Dict {ville, temperature, condition, date_prediction, raw_data} ou None.
    """
    coords = geocode_ville(ville, country_code)
    if not coords:
        return None

    lat, lon, nom = coords
    try:
        response = requests.get(
            OPENMETEO_FORECAST_URL,
            params={
                'latitude': lat,
                'longitude': lon,
                'current': ','.join([
                    'temperature_2m',
                    'relative_humidity_2m',
                    'apparent_temperature',
                    'precipitation',
                    'weather_code',
                    'wind_speed_10m',
                    'cloud_cover',
                ]),
                'hourly': 'temperature_2m,weather_code,precipitation_probability',
                'forecast_days': 1,
                'timezone': 'auto',
            },
            timeout=6,
        )
        response.raise_for_status()
        data = response.json()
        current = data.get('current') or {}
        temperature = float(current.get('temperature_2m'))
        weather_code = int(current.get('weather_code', 2))
        condition = _normaliser_condition(weather_code, temperature)

        return {
            'ville': ville or nom,
            'temperature': temperature,
            'condition': condition,
            'date_prediction': date.today(),
            'raw_data': data,
        }
    except (requests.RequestException, KeyError, TypeError, ValueError):
        return None


def sync_weather_for_city(ville: str = 'Antananarivo') -> bool:
    """Récupère la météo Open-Meteo et la sauvegarde en base."""
    weather_data = fetch_weather_from_api(ville)
    if not weather_data:
        return False

    enregistrer_meteo(
        ville=weather_data['ville'],
        temperature=weather_data['temperature'],
        condition=weather_data['condition'],
        date_prediction=weather_data['date_prediction'],
    )
    return True


def sync_weather_all_cities() -> list:
    """Synchronise la météo pour les principales villes malgaches."""
    villes = ['Antananarivo', 'Toamasina', 'Antsirabe', 'Mahajanga']
    results = []
    for ville in villes:
        success = sync_weather_for_city(ville)
        results.append({'ville': ville, 'success': success})
    return results
