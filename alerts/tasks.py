from celery import shared_task
from celery.utils.log import get_task_logger
from weather.models import Subscription, WeatherSnapshot, TelegramProfile
from .utils import matches_conditions
from botapp.sender import send_text_message

logger = get_task_logger(__name__)

@shared_task
def send_notifications():
    sent = 0
    subs = Subscription.objects.filter(is_active=True).select_related("user", "city")
    for sub in subs:
        last = WeatherSnapshot.objects.filter(city=sub.city).order_by("-ts").first()
        if not last:
            continue
        if not matches_conditions(last, sub.conditions or {}):
            continue
        tp = TelegramProfile.objects.filter(user=sub.user, is_confirmed=True, chat_id__isnull=False).first()
        if not tp:
            continue
        text = (
            f"<b>Погода в {sub.city.name}</b>\n"
            f"{last.ts:%d.%m %H:%M}\n"
            f"{last.description.capitalize()} | {last.temp}°C | влажн. {last.humidity}% | ветер {last.wind} м/с"
        )
        send_text_message(tp.chat_id, text)
        sent += 1
    logger.info("Notifications sent: %s", sent)
    return {"sent": sent}

from celery import shared_task

@shared_task
def ping():
    return "pong"