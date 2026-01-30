from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import logging

router = Router()

# Твой ID установлен
ADMIN_ID = 7105751841 

# --- ВСПОМОГАТЕЛЬНЫЕ ---

@router.message(Command("id"))
async def cmd_id(message: Message):
    await message.answer(f"Твой ID: `{message.from_user.id}`")

# --- УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ---

@router.message(Command("delete_user"))
async def cmd_delete_user(message: Message, db_session: AsyncSession):
    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Введи ID. Пример: `/delete_user 12345678`")
        return

    target_id = args[1]
    try:
        # Удаляем юзера по telegram_id
        result = await db_session.execute(
            text("DELETE FROM users WHERE telegram_id = :tid"),
            {"tid": int(target_id)}
        )
        await db_session.commit()

        if result.rowcount > 0:
            await message.answer(f"✅ Пользователь `{target_id}` полностью удален.")
        else:
            await message.answer("❌ Пользователь не найден.")
    except ValueError:
        await message.answer("❌ ID должен быть числом.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# --- ГЛОБАЛЬНЫЕ КОМАНДЫ ---

@router.message(Command("reset_all"))
async def cmd_reset_all(message: Message, db_session: AsyncSession):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        await db_session.execute(text("UPDATE users SET total_score = 0"))
        await db_session.commit()
        await message.answer("♻️ **РЕЙТИНГ ОБНУЛЕН!**\nВсе игроки сброшены до 0 очков.")
    except Exception as e:
        logging.error(f"Ошибка сброса: {e}")
        await message.answer(f"❌ Ошибка: {e}")

@router.message(Command("admin_stats"))
async def cmd_admin_stats(message: Message, db_session: AsyncSession):
    if message.from_user.id != ADMIN_ID:
        return

    result = await db_session.execute(text("SELECT COUNT(*) FROM users"))
    count = result.scalar()
    await message.answer(f"📊 **СТАТИСТИКА**\nВсего игроков в базе: `{count}`")

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, db_session: AsyncSession):
    if message.from_user.id != ADMIN_ID:
        return

    broadcast_text = message.text.replace("/broadcast", "").strip()
    if not broadcast_text:
        await message.answer("⚠️ Введи текст рассылки.")
        return

    result = await db_session.execute(text("SELECT telegram_id FROM users"))
    users = result.scalars().all()

    count = 0
    for user_id in users:
        try:
            await message.bot.send_message(chat_id=user_id, text=f"📢 **ОБЪЯВЛЕНИЕ:**\n\n{broadcast_text}")
            count += 1
        except Exception:
            pass 

    await message.answer(f"✅ Доставлено: `{count}` пользователям.")