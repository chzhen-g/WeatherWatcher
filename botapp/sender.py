import httpx
from django.conf import settings

def send_text_message(chat_id: str, text: str) -> None:
    token = settings.TELEGRAM_BOT_TOKEN
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    try:
        r = httpx.post(url, json=payload,timeout=15)
        r.raise_for_status()
    except httpx.HTTPError as e:
        print(f"Telegram send error: {e}")