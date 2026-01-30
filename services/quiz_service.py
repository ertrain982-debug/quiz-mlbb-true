from typing import List, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models import Question, User
import json

class QuizService:
    def __init__(self, db_session: AsyncSession, redis_client):
        self.db = db_session
        self.redis = redis_client
    
    async def get_random_questions(self, count: int = 5, telegram_id: int = None) -> List[Question]:
        # 1. Получаем список уже пройденных вопросов из Redis
        seen_questions = []
        if telegram_id:
            seen_data = await self.redis.client.get(f"seen_questions:{telegram_id}")
            if seen_data:
                seen_questions = json.loads(seen_data)
        
        # 2. Проверяем общее количество вопросов в базе
        total_stmt = select(func.count(Question.id))
        total_result = await self.db.execute(total_stmt)
        total_count = total_result.scalar()
        
        # Если пользователь прошёл почти всё — сбрасываем историю, чтобы не было пустых квизов
        if len(seen_questions) > (total_count - count):
            seen_questions = []
            if telegram_id:
                await self.redis.client.delete(f"seen_questions:{telegram_id}")
        
        # 3. Формируем запрос с исключением пройденных и случайным порядком
        stmt = select(Question)
        if seen_questions:
            stmt = stmt.where(Question.id.not_in(seen_questions))
        
        stmt = stmt.order_by(func.random()).limit(count)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def start_quiz(self, telegram_id: int, questions: List[Question]) -> None:
        quiz_data = {
            "questions": [q.id for q in questions],
            "current_index": 0,
            "score": 0,
            "correct_streak": 0,
            "correct_count": 0,
            "msg_to_delete": [], # Добавлено для синхронизации с хендлером
            "used_memes": []      # Добавлено для синхронизации с хендлером
        }
        await self.redis.client.setex(
            f"quiz:{telegram_id}",
            900,  # 15 минут TTL
            json.dumps(quiz_data)
        )
    
    async def get_quiz_state(self, telegram_id: int) -> Dict[str, Any] | None:
        data = await self.redis.client.get(f"quiz:{telegram_id}")
        return json.loads(data) if data else None
    
    async def update_quiz_state(self, telegram_id: int, quiz_data: Dict[str, Any]) -> None:
        ttl = await self.redis.client.ttl(f"quiz:{telegram_id}")
        if ttl > 0:
            await self.redis.client.setex(
                f"quiz:{telegram_id}",
                ttl,
                json.dumps(quiz_data)
            )
    
    async def finish_quiz(self, telegram_id: int, score: int, correct_count: int, question_ids: List[int]) -> None:
        # 1. Сохраняем новые пройденные вопросы в историю
        seen_data = await self.redis.client.get(f"seen_questions:{telegram_id}")
        seen_questions = json.loads(seen_data) if seen_data else []
        
        # Добавляем только новые ID
        for q_id in question_ids:
            if q_id not in seen_questions:
                seen_questions.append(q_id)
        
        # Обновляем историю в Redis на 30 дней
        await self.redis.client.setex(
            f"seen_questions:{telegram_id}",
            2592000, 
            json.dumps(seen_questions)
        )
        
        # 2. Обновляем статистику пользователя в БД
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            user.total_score += score
            user.games_played += 1
            user.correct_answers += correct_count
            await self.db.commit()
        
        # 3. Удаляем активную сессию квиза
        await self.redis.client.delete(f"quiz:{telegram_id}")
    
    async def get_question_by_id(self, question_id: int) -> Question | None:
        stmt = select(Question).where(Question.id == question_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()