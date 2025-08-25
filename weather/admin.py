from django.contrib import admin
from .models import City, WeatherSnapshot, TelegramProfile, Subscription, LinkToken


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "lat", "lon", "external_id")
    search_fields = ("name", "external_id")
    list_filter = ()
    ordering = ("name",)


@admin.register(WeatherSnapshot)
class WeatherSnapshotAdmin(admin.ModelAdmin):
    list_display = ("city", "ts", "temp", "humidity", "wind", "description")
    list_filter = ("city",)
    search_fields = ("city__name", "description")
    readonly_fields = ("raw",)
    date_hierarchy = "ts"


@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "chat_id", "is_confirmed")
    search_fields = ("user__username", "chat_id")
    list_filter = ("is_confirmed",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "city", "interval", "is_active", "created_at")
    list_filter = ("interval", "is_active", "city")
    search_fields = ("user__username", "city__name")
    autocomplete_fields = ("user", "city")

@admin.register(LinkToken)
class LinkTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "created_at", "expires_at")
    search_fields = ("user__username", "token")