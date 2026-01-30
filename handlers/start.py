from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import User
from redis_client import RedisClient

# Импортируем функции из других хендлеров
from handlers.quiz import cmd_quiz
from handlers.profile import cmd_profile
from handlers.rating import cmd_rating # Убедись, что функция в rating.py называется так

router = Router()

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎯 Викторина"), KeyboardButton(text="🖼 Угадай героя")],
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="🏆 Рейтинг")],
            [KeyboardButton(text="ℹ️ Правила")]
        ],
        resize_keyboard=True
    )

@router.message(Command("start"))
async def cmd_start(message: Message, db_session: AsyncSession):
    stmt = select(User).where(User.telegram_id == message.from_user.id)
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            telegram_id=message.from_user.id,
            username=message.from_user.username or "Gamer"
        )
        db_session.add(user)
        await db_session.commit()
        
        await message.answer(
            "🎮 Добро пожаловать в MLBB Quiz Bot!\n\n"
            "Выберите действие в меню ниже:",
            reply_markup=get_main_menu()
        )
    else:
        await message.answer(
            f"С возвращением, {message.from_user.first_name}!\n\n"
            f"Ваш счёт: {user.total_score} очков\n"
            f"Сыграно игр: {user.games_played}",
            reply_markup=get_main_menu()
        )

# --- ИСПРАВЛЕННЫЕ КНОПКИ ---

@router.message(F.text == "🎯 Викторина")
async def btn_quiz(message: Message, db_session: AsyncSession, redis_client: RedisClient):
    # Вместо простого текста вызываем саму функцию квиза
    await cmd_quiz(message, db_session, redis_client)

@router.message(F.text == "👤 Профиль")
async def btn_profile(message: Message, db_session: AsyncSession):
    # Вызываем функцию профиля
    await cmd_profile(message, db_session)

@router.message(F.text == "🏆 Рейтинг")
async def btn_rating(message: Message, db_session: AsyncSession):
    # Вызываем функцию рейтинга
    await cmd_rating(message, db_session)

@router.message(F.text == "🖼 Угадай героя")
async def btn_guess(message: Message):
    await message.answer("🚧 Режим «Угадай героя» в разработке! Скоро добавим!")

@router.message(F.text == "ℹ️ Правила")
async def btn_rules(message: Message):
    await message.answer(
        "📖 **ПРАВИЛА ВИКТОРИНЫ**\n\n"
        "🎯 **Викторина:**\n"
        "• 5 вопросов за игру\n"
        "• +10 очков за правильный ответ\n"
        "• 🔥 Бонус +10 за серию из 3-х правильных\n"
        "• ❌ -5 очков за неправильный ответ\n"
        "• ⏰ -10 очков за истечение времени (АФК)\n"
        "• ⏱ 15 секунд на каждый вопрос\n\n"
        "🏆 **Система рангов:**\n"
        "• 🛡 Воин: 0-100\n"
        "• ⚔️ Элита: 100-220\n"
        "• 🎖 Мастер: 220-400\n"
        "• 🛡 Грандмастер: 400-650\n"
        "• 💎 Эпик: 650-1100\n"
        "• 🦅 Легенда: 1100-1600\n"
        "• 🔮 Мифик: 1600-2500\n"
        "• 👑 Мифическая слава: 2500+\n\n"
        "Удачи в восхождении! 🎮",
        parse_mode="Markdown"
    )