from django.db import models
from django.contrib.auth import get_user_model
import uuid
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class City(models.Model):
    name = models.CharField('Название', max_length=120, db_index=True)
    external_id = models.CharField('Внешний ID', max_length=50, unique=True, null=True, blank=True)
    lat = models.FloatField('Широта')
    lon = models.FloatField('Долгота')

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['lat', 'lon']),
        ]

    def __str__(self):
        return f"{self.name} ({self.lat}, {self.lon})"


class WeatherSnapshot(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="snapshots", verbose_name="Город")
    ts = models.DateTimeField("Время среза", db_index=True)
    temp = models.FloatField("Температура, °C")
    humidity = models.IntegerField("Влажность, %")
    wind = models.FloatField("Скорость ветра, м/с")
    description = models.CharField("Описание", max_length=120)
    raw = models.JSONField("Ответ API")

    class Meta:
        verbose_name = "Снимок погоды"
        verbose_name_plural = "Снимки погоды"
        ordering = ["-ts"]
        indexes = [
            models.Index(fields=["city", "-ts"]),
        ]

    def __str__(self):
        return f"{self.city.name} @ {self.ts:%Y-%m-%d %H:%M} — {self.temp}°C"


class TelegramProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="telegram", verbose_name="Пользователь")
    chat_id = models.CharField("Chat ID", max_length=64, unique=True, null=True, blank=True)
    is_confirmed = models.BooleanField("Подтверждён", default=False)

    class Meta:
        verbose_name = "Telegram-профиль"
        verbose_name_plural = "Telegram-профили"

    def __str__(self):
        return f"{self.user} (chat_id={self.chat_id})"

class Subscription(models.Model):
    INTERVAL_HOURLY = "hourly"
    INTERVAL_DAILY = "daily"
    INTERVALS = [
        (INTERVAL_HOURLY, "Ежечасно"),
        (INTERVAL_DAILY, "Ежедневно"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions", verbose_name="Пользователь")
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="subscriptions", verbose_name="Город")
    interval = models.CharField("Интервал", max_length=10, choices=INTERVALS, default=INTERVAL_DAILY)
    conditions = models.JSONField("Условия", default=dict, blank=True)
    is_active = models.BooleanField("Активна", default=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        unique_together = ("user", "city")
        indexes = [
            models.Index(fields=["user", "city"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.user} → {self.city.name} ({self.interval})"

class LinkToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="link_token", verbose_name="Пользователь")
    token = models.CharField("Токен", max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    expires_at = models.DateTimeField("Истекает")

    class Meta:
        verbose_name = "Токен привязки Telegram"
        verbose_name_plural = "Токены привязки Telegram"

    def __str__(self):
        return f"{self.user} — {self.token}"

    @staticmethod
    def generate_for(user, ttl_minutes: int = 30):
        token = uuid.uuid4().hex
        obj, _ = LinkToken.objects.update_or_create(
            user=user,
            defaults={"token": token, "expires_at": timezone.now() + timedelta(minutes=ttl_minutes)},
        )
        return obj