# === 1) Инициализация Django ===
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

# === 2) Импорты после django.setup() ===
import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message
from django.conf import settings
from asgiref.sync import sync_to_async
from django.utils import timezone
from aiogram.filters import Command, CommandStart, CommandObject
import shlex

from weather.models import LinkToken, TelegramProfile, City, Subscription

# === 3) Логи ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bot")

# === 4) Aiogram v3: Bot + Dispatcher + Router ===
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
router = Router()

@router.message(CommandStart())
async def cmd_start(m: Message):
    await m.answer(
        "Привет! Чтобы привязать аккаунт, зайдите на сайт → «Мой токен» и пришлите сюда:\n"
        "/link <ваш_токен>\n\n"
        "Для проверки работоспособности есть команда: /ping"
    )

@router.message(Command('ping'))
async def cmd_ping(m: Message):
    await m.answer("pong ✅")

@router.message(F.text.startswith("/link"))
async def cmd_link(m: Message):
    parts = m.text.split(maxsplit=1)
    if len(parts) < 2:
        await m.answer("Укажите токен: /link <токен>")
        return
    token = parts[1].strip()

    lt = await sync_to_async(LinkToken.objects.filter(token=token).select_related("user").first)()
    if not lt:
        await m.answer("Неверный токен.")
        return
    if lt.expires_at <= timezone.now():
        await m.answer("Токен истёк. Сгенерируйте новый на сайте.")
        return

    # БЫЛО async def _do_link(): ... -> ДОЛЖНО БЫТЬ обычное def
    def _do_link():
        tp, _ = TelegramProfile.objects.get_or_create(user=lt.user)
        tp.chat_id = str(m.chat.id)
        tp.is_confirmed = True
        tp.save()
        lt.delete()

    await sync_to_async(_do_link, thread_sensitive=True)()
    await m.answer("Готово! Аккаунт привязан ✅")

async def main():
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook cleared (if was set).")
    except Exception as e:
        logger.warning("Webhook clear failed: %s", e)

    dp.include_router(router)
    logger.info("Bot is starting polling…")
    await dp.start_polling(bot)

def parse_city_and_kv(argstr: str) -> tuple[str, dict]:
    """
    Преобразует строку аргументов в (city, kv_dict).
    Пример: 'New York interval=daily temp_below=-5 rain=1'
      -> city='New York', kv={'interval':'daily','temp_below':'-5','rain':'1'}
    """
    tokens = shlex.split(argstr) if argstr else []
    if not tokens:
        return "", {}

    # Город = все токены до ПЕРВОГО токена с '='
    city_parts = []
    i = 0
    for i, t in enumerate(tokens):
        if "=" in t:
            break
        city_parts.append(t)
    else:
        # ни одного key=value — город = все токены
        return " ".join(city_parts).strip(), {}

    city = " ".join(city_parts).strip()
    kv_tokens = tokens[i:]  # всё, включая первый key=value

    kv = {}
    for part in kv_tokens:
        if "=" in part:
            k, v = part.split("=", 1)
            kv[k.strip()] = v.strip()
    return city, kv

@router.message(F.text == "/cities")
async def cmd_cities(m: Message):
    qs = await sync_to_async(lambda: list(City.objects.order_by("name").values_list("name", flat=True)))()
    if not qs:
        await m.answer("Пока нет городов. Добавьте их в админке.")
        return
    text = "Доступные города:\n" + "\n".join(f"• {name}" for name in qs)
    await m.answer(text)

@router.message(Command("status"))
async def cmd_status(m: Message):
    def _get():
        from weather.models import TelegramProfile, Subscription
        tp = (TelegramProfile.objects
              .filter(chat_id=str(m.chat.id), is_confirmed=True)
              .select_related("user").first())
        if not tp:
            return None, []
        subs = list(Subscription.objects.filter(user=tp.user).select_related("city"))
        return tp, subs

    tp, subs = await sync_to_async(_get, thread_sensitive=True)()
    if not tp:
        await m.answer("Сначала привяжите аккаунт: /start → /link <токен>.")
        return
    if not subs:
        await m.answer("У вас нет подписок. Создайте: /sub <город> interval=daily …")
        return

    lines = ["Ваши подписки:"]
    for s in subs:
        cond = s.conditions or {}
        parts = []
        if "temp_below" in cond: parts.append(f"<{cond['temp_below']}°C")
        if "temp_above" in cond: parts.append(f">{cond['temp_above']}°C")
        if cond.get("rain"): parts.append("дождь")
        cstr = ", ".join(parts) if parts else "(нет)"
        lines.append(f"• {s.city.name}: {s.interval}, {cstr}, {'on' if s.is_active else 'off'}")
    await m.answer("\n".join(lines))

@router.message(Command("off"))
async def cmd_off(m: Message, command: CommandObject):
    city_name = (command.args or "").strip()
    if not city_name:
        await m.answer("Формат: /off <город>")
        return

    def _off():
        from weather.models import TelegramProfile, City, Subscription
        tp = (TelegramProfile.objects
              .filter(chat_id=str(m.chat.id), is_confirmed=True)
              .select_related("user").first())
        if not tp:
            return "Сначала привяжите аккаунт: /start → /link <токен>."
        city = City.objects.filter(name__iexact=city_name).first()
        if not city:
            return f"Город '{city_name}' не найден."
        sub = Subscription.objects.filter(user=tp.user, city=city).first()
        if not sub:
            return "У вас нет подписки на этот город."
        sub.is_active = False
        sub.save()
        return f"Подписка на {city.name} выключена."

    msg = await sync_to_async(_off, thread_sensitive=True)()
    await m.answer(msg)

@router.message(Command("sub"))
async def cmd_sub(m: Message, command: CommandObject):
    args = (command.args or "").strip()
    if not args:
        await m.answer("Формат: /sub <город> [interval=hourly|daily] [temp_below=-10] [temp_above=30] [rain=1]")
        return

    city_name, kv = parse_city_and_kv(args)
    if not city_name:
        await m.answer("Не удалось распознать город. Пример: /sub Almaty interval=daily")
        return

    def _create_or_update():
        from weather.models import TelegramProfile, City, Subscription
        tp = (TelegramProfile.objects
              .filter(chat_id=str(m.chat.id), is_confirmed=True)
              .select_related("user").first())
        if not tp:
            return "Сначала привяжите аккаунт: /start → /link <токен>."

        city = City.objects.filter(name__iexact=city_name).first()
        if not city:
            return f"Город '{city_name}' не найден. Посмотрите /cities"

        interval = kv.get("interval", Subscription.INTERVAL_DAILY)
        if interval not in dict(Subscription.INTERVALS):
            interval = Subscription.INTERVAL_DAILY

        conditions = {}
        if "temp_below" in kv:
            try: conditions["temp_below"] = float(kv["temp_below"])
            except ValueError: pass
        if "temp_above" in kv:
            try: conditions["temp_above"] = float(kv["temp_above"])
            except ValueError: pass
        if str(kv.get("rain", "")).lower() in ("1", "true", "yes", "on"):
            conditions["rain"] = True

        sub, created = Subscription.objects.get_or_create(
            user=tp.user, city=city,
            defaults={"interval": interval, "conditions": conditions, "is_active": True}
        )
        if not created:
            sub.interval = interval
            sub.conditions = conditions
            sub.is_active = True
            sub.save()
            return f"Подписка обновлена: {city.name} ({interval})"
        return f"Подписка создана: {city.name} ({interval})"

    msg = await sync_to_async(_create_or_update, thread_sensitive=True)()
    await m.answer(msg)

if __name__ == "__main__":
    try:
        if not settings.TELEGRAM_BOT_TOKEN or "123:ABC" in settings.TELEGRAM_BOT_TOKEN:
            raise RuntimeError("TELEGRAM_BOT_TOKEN не задан или заглушка. Проверь .env.")
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
    except Exception as e:
        logger.exception("Fatal error: %s", e)
