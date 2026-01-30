from dataclasses import dataclass
from os import getenv
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    BOT_TOKEN: str
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


def load_config() -> Config:
    return Config(
        BOT_TOKEN=getenv("BOT_TOKEN"),
        DB_HOST=getenv("DB_HOST", "localhost"),
        DB_PORT=int(getenv("DB_PORT", 5432)),
        DB_USER=getenv("DB_USER"),
        DB_PASSWORD=getenv("DB_PASSWORD"),
        DB_NAME=getenv("DB_NAME"),
        REDIS_HOST=getenv("REDIS_HOST", "localhost"),
        REDIS_PORT=int(getenv("REDIS_PORT", 6379)),
        REDIS_DB=int(getenv("REDIS_DB", 0))
    )