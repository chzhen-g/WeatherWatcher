from django import forms
from .models import Subscription, City

class SubscriptionForm(forms.Form):
    city = forms.ModelChoiceField(queryset=City.objects.all().order_by("name"), label="Город")
    interval = forms.ChoiceField(
        choices=Subscription.INTERVALS,
        initial=Subscription.INTERVAL_DAILY,
        label="Частота"
    )
    temp_below = forms.FloatField(label="Темп. ниже, °C", required=False)
    temp_above = forms.FloatField(label="Темп. выше, °C", required=False)
    rain = forms.BooleanField(label="Уведомлять если идет дождь", required=False)

    def to_conditions(self):
        data = self.cleaned_data
        cond = {}
        if data.get("temp_below") is not None:
            cond["temp_below"] = data["temp_below"]
        if data.get("temp_above") is not None:
            cond["temp_above"] = data["temp_above"]
        if data.get("rain"):
            cond["rain"] = True
        return cond

