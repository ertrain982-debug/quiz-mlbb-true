import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command # Добавили импорт для команд
from config import load_config
from database import Database
from redis_client import RedisClient
from handlers import routers
# Импортируем админский роутер напрямую, если его нет в списке routers
from handlers.admin import router as admin_router 

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    config = load_config()
    
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    db = Database(config)
    await db.init_db()
    
    redis_client = RedisClient(config)
    
    # 1. Сначала подключаем админский роутер (приоритет выше)
    dp.include_router(admin_router)
    
    # 2. Подключаем остальные роутеры из твоего списка
    for router in routers:
        dp.include_router(router)
    
    @dp.update.middleware()
    async def db_session_middleware(handler, event, data):
        async with db.get_session() as session:
            data["db_session"] = session
            data["redis_client"] = redis_client
            return await handler(event, data)
    
    try:
        # Удаляем вебхук перед запуском (помогает избежать ошибок конфликта)
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await redis_client.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())