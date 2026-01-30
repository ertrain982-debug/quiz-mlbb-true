import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Загружаем .env (для локальной разработки), на Railway подтянутся Variables
load_dotenv()

@dataclass
class Config:
    BOT_TOKEN: str
    DATABASE_URL: str
    REDIS_URL: str

    @property
    def database_url(self) -> str:
        """Исправляет ссылку для SQLAlchemy, если она пришла от Railway"""
        if self.DATABASE_URL and self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.DATABASE_URL

def load_config() -> Config:
    # Берем токен и сразу очищаем его от пробелов и переносов строк
    raw_token = os.getenv("BOT_TOKEN")
    clean_token = raw_token.strip() if raw_token else ""
    
    return Config(
        BOT_TOKEN=clean_token,
        DATABASE_URL=os.getenv("DATABASE_URL"),
        REDIS_URL=os.getenv("REDIS_URL")
    )
