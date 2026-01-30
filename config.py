import os
from dataclasses import dataclass
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

@dataclass
class Config:
    BOT_TOKEN: str
    DATABASE_URL: str
    REDIS_URL: str

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL and self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.DATABASE_URL

    # Добавляем свойства, которые ищет твой redis_client.py
    @property
    def REDIS_HOST(self) -> str:
        return urlparse(self.REDIS_URL).hostname or "localhost"

    @property
    def REDIS_PORT(self) -> int:
        return urlparse(self.REDIS_URL).port or 6379

def load_config() -> Config:
    raw_token = os.getenv("BOT_TOKEN")
    clean_token = raw_token.strip() if raw_token else ""
    
    return Config(
        BOT_TOKEN=clean_token,
        DATABASE_URL=os.getenv("DATABASE_URL"),
        REDIS_URL=os.getenv("REDIS_URL")
    )

