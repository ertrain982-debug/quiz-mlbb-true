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
        """Для SQLAlchemy"""
        if self.DATABASE_URL and self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.DATABASE_URL

    # Разбираем REDIS_URL на части для старого кода
    @property
    def REDIS_HOST(self) -> str:
        return urlparse(self.REDIS_URL).hostname or "localhost"

    @property
    def REDIS_PORT(self) -> int:
        return urlparse(self.REDIS_URL).port or 6379

    @property
    def REDIS_PASSWORD(self) -> str:
        return urlparse(self.REDIS_URL).password

    @property
    def REDIS_DB(self) -> int:
        path = urlparse(self.REDIS_URL).path
        try:
            return int(path.replace('/', '')) if path else 0
        except ValueError:
            return 0

def load_config() -> Config:
    raw_token = os.getenv("BOT_TOKEN")
    clean_token = raw_token.strip() if raw_token else ""
    
    return Config(
        BOT_TOKEN=clean_token,
        DATABASE_URL=os.getenv("DATABASE_URL"),
        REDIS_URL=os.getenv("REDIS_URL")
    )
