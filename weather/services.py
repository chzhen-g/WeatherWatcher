import httpx
from django.conf import settings

OWM_CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"

class WeatherApiError(Exception):
    pass

def fetch_current_by_coords(lat: float, lon: float, timeout: int = 15, lang: str = "ru", units: str = "metric") -> dict:
    """Запрос текущей погоды по координатам."""
    params = {
        "lat": lat,
        "lon": lon,
        "appid": settings.OWM_API_KEY,
        "units": units,
        "lang": lang,
    }
    try:
        r = httpx.get(OWM_CURRENT_URL, params=params, timeout=timeout)
        r.raise_for_status()
    except httpx.HTTPError as e:
        raise WeatherApiError(f"OpenWeather error: {e}") from e
    return r.json()
