from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from services.rating_service import RatingService

router = Router()


@router.message(Command("rating"))
async def cmd_rating(message: Message, db_session: AsyncSession):
    service = RatingService(db_session)
    top_users = await service.get_top_users(20)
    
    if not top_users:
        await message.answer("🏆 Рейтинг пока пуст. Будьте первым!")
        return
    
    text = "🏆 Топ-20 игроков:\n\n"
    for i, user in enumerate(top_users, 1):
        username = user.username or f"User{user.telegram_id}"
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} {username} — {user.total_score} очков\n"
    
    await message.answer(text)