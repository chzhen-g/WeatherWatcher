from django.urls import path
from . import views

app_name = "weather"

urlpatterns = [
    path("", views.index, name="index"),
    path("city/<int:pk>/", views.city_detail, name="city_detail"),
    path("me/token/", views.my_token, name="my_token"),
    path("me/subscriptions/", views.my_subscriptions, name="my_subscriptions"),
    path("me/subscriptions/create/", views.subscription_create, name="subscription_create"),
    path("me/subscriptions/<int:pk>/edit/", views.subscription_edit, name="subscription_edit"),
    path("me/subscriptions/<int:pk>/delete/", views.subscription_delete, name="subscription_delete"),
]

