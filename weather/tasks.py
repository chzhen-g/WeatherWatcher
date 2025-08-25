from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import transaction
from .models import City
from .services import fetch_current_by_coords, WeatherApiError
from .repo import save_snapshot

logger = get_task_logger(__name__)

@shared_task(bind=True, autoretry_for=(WeatherApiError,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def fetch_onecall_for_all_cities(self, exclude: str | None = "minutely,alerts"):
    """
    Получить One Call для всех городов и сохранить снимок из 'current'.
    exclude по умолчанию отрезает шумные секции на dev.
    """
    saved = 0
    for city in City.objects.all():
        try:
            data = fetch_current_by_coords(city.lat, city.lon)
            with transaction.atomic():
                save_snapshot(city, data)
            saved += 1
            logger.info("Saved snapshot (One Call) for %s", city.name)
        except Exception as e:
            logger.exception("Failed for %s: %s", city.name, e)
            continue
    return {"saved": saved}
