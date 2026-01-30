from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession
from services.rating_service import RatingService
from services.rank_service import get_rank_data

router = Router()

@router.message(Command("profile"))
async def cmd_profile(message: Message, db_session: AsyncSession):
    service = RatingService(db_session)
    user = await service.get_user_profile(message.from_user.id)
    
    if not user:
        await message.answer("❌ Профиль не найден. Используйте /start для регистрации.")
        return
    
    # Получаем данные ранга
    rank_name, rank_emoji, rank_image = get_rank_data(user.total_score)
    
    total_questions = user.games_played * 5
    accuracy = (user.correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    text = (
        f"👤 **Ваш профиль:**\n\n"
        f"{rank_emoji} **Ранг:** {rank_name}\n"
        f"🎯 **Очки:** {user.total_score}\n"
        f"🎮 **Сыграно игр:** {user.games_played}\n"
        f"✅ **Правильных ответов:** {user.correct_answers}/{total_questions}\n"
        f"📊 **Точность:** {accuracy:.1f}%\n"
        f"📅 **Дата регистрации:** {user.created_at.strftime('%d.%m.%Y')}"
    )

    await message.answer_photo(
        photo=FSInputFile(rank_image),
        caption=text,
        parse_mode="Markdown"
    )