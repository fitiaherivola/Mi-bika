"""
Compatibilité : OpenWeatherMap a été remplacé par Open-Meteo.
Les imports historiques restent valides.
"""

from weather.services.openmeteo import (  # noqa: F401
    fetch_weather_from_api,
    sync_weather_for_city,
    sync_weather_all_cities,
)
