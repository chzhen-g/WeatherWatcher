from django.shortcuts import render, get_object_or_404, redirect
from .models import City, WeatherSnapshot, LinkToken, Subscription
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse
from .forms import SubscriptionForm


def index(request):
    cities = City.objects.all().order_by("name")
    return render(request, "weather/index.html", {"cities": cities})

def city_detail(request, pk: int):
    city = get_object_or_404(City, pk=pk)
    snaps = WeatherSnapshot.objects.filter(city=city).order_by("-ts")[:50]
    return render(request, "weather/city_detail.html", {"city": city, "snaps": snaps})

@login_required
def my_token(request):
    lt = getattr(request.user, "link_token", None)
    if not lt or lt.expires_at <= timezone.now():
        lt = LinkToken.generate_for(request.user, ttl_minutes=30)
    return render(request, "weather/my_token.html", {"token": lt.token, "expires_at": lt.expires_at})

@login_required()
def my_subscriptions(request):
    subs = Subscription.objects.filter(user=request.user).select_related("city").order_by("city__name")
    return render(request, "weather/my_subscriptions.html", {"subs": subs})

@login_required
def subscription_create(request):
    if request.method == "POST":
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            city = form.cleaned_data["city"]
            sub, created = Subscription.objects.get_or_create(
                user=request.user,
                city=city,
                defaults={
                    "interval": form.cleaned_data["interval"],
                    "conditions": form.to_conditions(),
                    "is_active": True,
                },
            )
            if not created:
                sub.interval = form.cleaned_data["interval"]
                sub.conditions = form.to_conditions()
                sub.is_active = True
                sub.save()
            return HttpResponseRedirect(reverse("weather:my_subscriptions"))
    else:
        form = SubscriptionForm()
    return render(request, "weather/subscription_form.html", {"form": form, "mode": "create"})

@login_required
def subscription_edit(request, pk: int):
    sub = get_object_or_404(Subscription, pk=pk)
    if sub.user != request.user:
        return HttpResponseForbidden("Нет доступа.")
    initial = {
        "city": sub.city_id,
        "interval": sub.interval,
        "temp_below": (sub.conditions or {}).get("temp_below"),
        "temp_above": (sub.conditions or {}).get("temp_above"),
        "rain": (sub.conditions or {}).get("rain", False),
    }
    if request.method == "POST":
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            sub.city = form.cleaned_data["city"]
            sub.interval = form.cleaned_data["interval"]
            sub.conditions = form.to_conditions()
            sub.save()
            return HttpResponseRedirect(reverse("weather:my_subscriptions"))
    else:
        form = SubscriptionForm(initial=initial)
    return render(request, "weather/subscription_form.html", {"form": form, "mode": "edit", "sub": sub})

@login_required
def subscription_delete(request, pk: int):
    sub = get_object_or_404(Subscription, pk=pk)
    if sub.user != request.user:
        return HttpResponseForbidden("Нет доступа.")
    if request.method == "POST":
        sub.delete()
        return HttpResponseRedirect(reverse("weather:my_subscriptions"))
    return render(request, "weather/subscription_delete.html", {"sub": sub})