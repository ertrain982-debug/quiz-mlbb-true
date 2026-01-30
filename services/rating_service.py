from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import User


class RatingService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def get_top_users(self, limit: int = 20) -> List[User]:
        stmt = (
            select(User)
            .order_by(User.total_score.desc(), User.created_at.asc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_user_profile(self, telegram_id: int) -> User | None:
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()