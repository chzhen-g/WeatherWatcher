from django.utils import timezone
from .models import WeatherSnapshot, City

def save_snapshot(city: City, data: dict) -> WeatherSnapshot:
    return WeatherSnapshot.objects.create(
        city=city,
        ts=timezone.now(),
        temp=data["main"]["temp"],
        humidity=data["main"]["humidity"],
        wind=data["wind"]["speed"],
        description=data["weather"][0]["description"],
        raw=data,
    )
