import os
import logging
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
OWNER_ID_RAW = os.getenv("OWNER_ID", "").strip()

if not BOT_TOKEN:
    raise RuntimeError("Не задан BOT_TOKEN в файле .env")
if not OWNER_ID_RAW.isdigit():
    raise RuntimeError("Укажи числовой OWNER_ID в файле .env")

OWNER_ID = int(OWNER_ID_RAW)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Stake pay запущен.\n"
        "Команда владельца: /send USER_ID GIFT_ID\n"
        "Пример: /send 123456789 gift_id"
    )


@dp.message(Command("send"))
async def send_gift(message: Message):
    # Команду может выполнять только владелец бота.
    if message.from_user is None or message.from_user.id != OWNER_ID:
        await message.answer("⛔ Эта команда доступна только владельцу бота.")
        return

    parts = (message.text or "").split()
    if len(parts) != 3:
        await message.answer(
            "Использование:\n/send USER_ID GIFT_ID\n\n"
            "USER_ID — числовой Telegram ID получателя.\n"
            "GIFT_ID — идентификатор подарка из get_available_gifts."
        )
        return

    recipient_raw, gift_id = parts[1], parts[2]
    if not recipient_raw.isdigit():
        await message.answer("❌ USER_ID должен быть числом.")
        return

    recipient_id = int(recipient_raw)

    try:
        # Текст будет прикреплён к подарку, если этот параметр поддерживается
        # текущей версией Bot API и доступен для выбранного типа подарка.
        await bot.send_gift(
            user_id=recipient_id,
            gift_id=gift_id,
            text="Подарок моему создателю"
        )
        await message.answer("✅ Подарок успешно отправлен!")
    except (TelegramBadRequest, TelegramForbiddenError) as e:
        logging.warning("Telegram не отправил подарок: %s", e)
        await message.answer(
            "❌ Telegram не смог отправить подарок.\n"
            f"Причина: {e}\n\n"
            "Проверь USER_ID, GIFT_ID, доступность подарка и баланс Telegram Stars."
        )
    except Exception:
        logging.exception("Ошибка при отправке подарка")
        await message.answer("❌ Произошла внутренняя ошибка. Подробности смотри в консоли.")


@dp.message(Command("gifts"))
async def gifts(message: Message):
    if message.from_user is None or message.from_user.id != OWNER_ID:
        await message.answer("⛔ Команда доступна только владельцу.")
        return

    try:
        available = await bot.get_available_gifts()
        if not available.gifts:
            await message.answer("Сейчас доступных подарков нет.")
            return

        lines = ["🎁 Доступные подарки:"]
        for gift in available.gifts:
            lines.append(
                f"ID: {gift.id} | Цена: {gift.star_count} Stars"
            )
        await message.answer("\n".join(lines))
    except Exception as e:
        logging.exception("Не удалось получить список подарков")
        await message.answer(f"❌ Не удалось получить подарки: {e}")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
