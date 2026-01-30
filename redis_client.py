import redis.asyncio as redis
from config import Config


class RedisClient:
    def __init__(self, config: Config):
        self.client = redis.Redis(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            password=config.REDIS_PASSWORD,  # Вот этой строчки не хватало
            decode_responses=True
        )
    
    async def close(self):
        await self.client.close()
