# WeatherWatcher 🌤️

A **Django + Celery + Telegram Bot** project for monitoring weather in different cities with customizable notifications.

## 🚀 Features
- User registration & authentication (Django built-in)
- Admin panel for managing cities and weather snapshots
- Periodic weather data collection from [OpenWeather API](https://openweathermap.org/api)
- Weather history for each city (with temperature, humidity, wind, description)
- Telegram bot integration:
  - `/start` — link your Telegram account with the website using a one-time token
  - `/cities` — list available cities
  - `/sub <city> ...` — subscribe to weather updates with conditions
  - `/status` — view your subscriptions
  - `/off <city>` — disable subscription
- Flexible subscription conditions:
  - Notify when temperature is below/above a threshold
  - Notify when it rains
  - Daily or hourly frequency
- Asynchronous tasks with Celery & Redis

---

## 🛠 Tech Stack
- **Backend**: Django 5.x, Django ORM
- **Database**: SQLite (for development) / PostgreSQL (production)
- **Async tasks**: Celery + Redis
- **Telegram bot**: [aiogram v3](https://docs.aiogram.dev/en/latest/)
- **HTTP client**: httpx
- **Config**: django-environ (`.env`)

---

## 📂 Project Structure
