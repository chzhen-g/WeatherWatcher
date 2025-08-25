from django.core.management.base import BaseCommand, CommandError
from weather.models import City
from weather.services import fetch_current_by_coords, WeatherApiError
from weather.repo import save_snapshot

class Command(BaseCommand):
    help = "Разовый сбор текущей погоды для указанного города или для всех городов."

    def add_arguments(self, parser):
        parser.add_argument("--city", type=str, help="Имя города (точное совпадение). Если не указано — для всех.")

    def handle(self, *args, **options):
        name = options.get("city")
        qs = City.objects.all()
        if name:
            city = qs.filter(name__iexact=name).first()
            if not city:
                raise CommandError(f"Город '{name}' не найден.")
            qs = [city]
        saved = 0
        for city in qs:
            try:
                data = fetch_current_by_coords(city.lat, city.lon)
                save_snapshot(city, data)
                self.stdout.write(self.style.SUCCESS(f"OK: {city.name}"))
                saved += 1
            except WeatherApiError as e:
                self.stdout.write(self.style.ERROR(f"API error for {city.name}: {e}"))
        self.stdout.write(self.style.NOTICE(f"Saved snapshots: {saved}"))
