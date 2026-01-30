import random
import time
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession
from services.quiz_service import QuizService
from redis_client import RedisClient
from services.rank_service import get_rank_data
from services.rating_service import RatingService

router = Router()

async def start_quiz_process(user_id: int, message: Message, db_session: AsyncSession, redis_client: RedisClient):
    service = QuizService(db_session, redis_client)
    await redis_client.client.delete(f"quiz:{user_id}")
    await redis_client.client.delete(f"quiz_state:{user_id}")
    
    questions = await service.get_random_questions(5, telegram_id=user_id) 
    
    if not questions or len(questions) < 5:
        await message.answer("❌ Недостаточно вопросов в базе данных.")
        return
    
    await service.start_quiz(user_id, questions)
    
    quiz_state = await service.get_quiz_state(user_id)
    quiz_state.update({
        "used_memes": [],
        "msg_to_delete": [],
        "current_index": 0,
        "score": 0,
        "correct_count": 0,
        "correct_streak": 0
    })
    await service.update_quiz_state(user_id, quiz_state)
    await send_question(message, service, user_id, 0)

@router.message(Command("quiz"))
@router.message(F.text == "🎯 Викторина")
async def cmd_quiz(message: Message, db_session: AsyncSession, redis_client: RedisClient):
    await start_quiz_process(message.from_user.id, message, db_session, redis_client)

async def send_question(message: Message, service: QuizService, telegram_id: int, index: int):
    quiz_state = await service.get_quiz_state(telegram_id)
    if not quiz_state: return
    
    question_id = quiz_state["questions"][index]
    question = await service.get_question_by_id(question_id)
    if not question: return

    # Короткие ответы для кнопок
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"A) {question.option_a}", callback_data=f"answer:A:{index}"),
            InlineKeyboardButton(text=f"B) {question.option_b}", callback_data=f"answer:B:{index}")
        ],
        [
            InlineKeyboardButton(text=f"C) {question.option_c}", callback_data=f"answer:C:{index}"),
            InlineKeyboardButton(text=f"D) {question.option_d}", callback_data=f"answer:D:{index}")
        ]
    ])
    
    all_memes = list(range(1, 30))
    available_memes = [m for m in all_memes if m not in quiz_state.get("used_memes", [])]
    meme_number = random.choice(available_memes or all_memes)
    quiz_state.setdefault("used_memes", []).append(meme_number)
    
    photo = FSInputFile(f"images/meme{meme_number}.jpg")
    caption_text = (
        f"❓ Вопрос {index + 1}/5\n📂 Категория: {question.category}\n\n"
        f"**{question.question_text}**\n\n⏱ У вас 15 секунд!"
    )
    
    msg = await message.answer_photo(photo=photo, caption=caption_text, reply_markup=keyboard)
    
    quiz_state.setdefault("msg_to_delete", []).append(msg.message_id)
    quiz_state["q_start_time"] = time.time() 
    await service.update_quiz_state(telegram_id, quiz_state)

@router.callback_query(F.data.startswith("answer:"))
async def process_answer(callback: CallbackQuery, db_session: AsyncSession, redis_client: RedisClient):
    service = QuizService(db_session, redis_client)
    rating_service = RatingService(db_session)
    
    parts = callback.data.split(":")
    user_answer, question_index = parts[1], int(parts[2])
    
    quiz_state = await service.get_quiz_state(callback.from_user.id)
    if not quiz_state or quiz_state["current_index"] != question_index:
        await callback.answer("Сессия истекла!")
        return

    # Логика таймера
    if time.time() - quiz_state.get("q_start_time", 0) > 15:
        await callback.answer("⏰ Время вышло! Штраф -10", show_alert=True)
        quiz_state["score"] -= 10
        quiz_state["correct_streak"] = 0
        await service.update_quiz_state(callback.from_user.id, quiz_state)
        
        next_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Пропустить", callback_data=f"timeout_next:{question_index}")]
        ])
        try:
            await callback.message.edit_caption(caption=f"{callback.message.caption}\n\n⏰ **АФК! -10 очков**", reply_markup=next_kb)
        except TelegramBadRequest: pass
        return

    question = await service.get_question_by_id(quiz_state["questions"][question_index])
    is_correct = user_answer == question.correct_option
    
    if is_correct:
        quiz_state["score"] += 10
        quiz_state["correct_count"] += 1
        quiz_state["correct_streak"] += 1
        result_text = "✅ Правильно! +10 очков"
        if quiz_state["correct_streak"] == 3:
            quiz_state["score"] += 10
            result_text += "\n🔥 СЕРИЯ! Бонус +10!"
    else:
        quiz_state["score"] -= 5
        quiz_state["correct_streak"] = 0
        result_text = f"❌ Ошибка! -5 очков\nОтвет: {question.correct_option}"
    
    try:
        await callback.message.edit_caption(caption=f"{callback.message.caption}\n\n{result_text}", reply_markup=None)
    except TelegramBadRequest: pass

    await next_step(callback, quiz_state, service, rating_service)
    await callback.answer()

@router.callback_query(F.data.startswith("timeout_next:"))
async def process_timeout_next(callback: CallbackQuery, db_session: AsyncSession, redis_client: RedisClient):
    service = QuizService(db_session, redis_client)
    quiz_state = await service.get_quiz_state(callback.from_user.id)
    if quiz_state:
        try: await callback.message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest: pass
        await next_step(callback, quiz_state, service, RatingService(db_session))
    await callback.answer()

async def next_step(callback, quiz_state, service, rating_service):
    quiz_state["current_index"] += 1
    
    if quiz_state["current_index"] >= 5:
        # Очистка старых сообщений
        for msg_id in quiz_state.get("msg_to_delete", []):
            try: await callback.bot.delete_message(callback.message.chat.id, msg_id)
            except TelegramBadRequest: pass
        
        user = await rating_service.get_user_profile(callback.from_user.id)
        old_rank, _, _ = get_rank_data(user.total_score if user else 0)

        # Сохранение и расчет итогов
        await service.finish_quiz(callback.from_user.id, quiz_state["score"], quiz_state["correct_count"], quiz_state["questions"])
        
        updated_user = await rating_service.get_user_profile(callback.from_user.id)
        new_rank, rank_emoji, rank_image = get_rank_data(updated_user.total_score)

        status = "Твой ранг растет! 📈" if quiz_state['score'] > 0 else "Нужно больше практики! 🛡"
        final_text = (
            f"🎉 **КВИЗ ЗАВЕРШЁН!**\n\n"
            f"📊 Итог раунда: `{quiz_state['score']}` очков\n"
            f"✅ Правильно: {quiz_state['correct_count']}/5\n\n"
            f"{status}"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎮 Играть снова", callback_data="start_new_quiz")]])
        await callback.message.answer(final_text, reply_markup=kb)

        if new_rank != old_rank:
            await callback.message.answer_photo(photo=FSInputFile(rank_image), 
                                             caption=f"🎊 **НОВЫЙ РАНГ!**\nТвой ранг: {rank_emoji} **{new_rank}**!")
    else:
        await service.update_quiz_state(callback.from_user.id, quiz_state)
        await send_question(callback.message, service, callback.from_user.id, quiz_state["current_index"])

@router.callback_query(F.data == "start_new_quiz")
async def fast_quiz_start(callback: CallbackQuery, db_session: AsyncSession, redis_client: RedisClient):
    try: await callback.message.delete()
    except TelegramBadRequest: pass
    await start_quiz_process(callback.from_user.id, callback.message, db_session, redis_client)
    await callback.answer()