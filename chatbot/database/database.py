"""
База данных для чат-бота (отдельная от CraftCards)
Хранит кеш пользователей, логи команд и настройки
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, event
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager
from datetime import datetime
import os

from chatbot.constants.cnst_Server import BASE_DIR

# Путь к БД чат-бота
DB_NAME = os.path.join(BASE_DIR, "chatbot.db")
db_uri = f'sqlite+aiosqlite:///{DB_NAME}'

print(f"[ChatBot DB] Connecting to: {db_uri}")

engine = create_async_engine(
    db_uri,
    connect_args={'timeout': 30},
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

Base = declarative_base()


# --- Модели ---

class ChatUser(Base):
    """Пользователи чата (кеш)"""
    __tablename__ = 'chat_users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nick = Column(String(255), unique=True, nullable=False, index=True)
    vk_id = Column(String(255), nullable=True, index=True)  # Связь с CraftCards
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_registered = Column(Boolean, default=False)  # Зарегистрирован в CraftCards


class ViewerSession(Base):
    """Сессии зрителей на стриме"""
    __tablename__ = 'viewer_sessions'
    
    vk_id = Column(Integer, primary_key=True)
    nickname = Column(String(255), nullable=False)
    session_start = Column(DateTime, nullable=False)
    last_seen = Column(DateTime, nullable=False)
    total_minutes = Column(Integer, default=0)
    ac_earned = Column(Integer, default=0)
    last_ac_bonus_at = Column(DateTime, nullable=True)
    milestones_achieved = Column(Text, default='[]')  # JSON список [15, 30, 60, 180]


class CommandLog(Base):
    """Лог команд пользователей"""
    __tablename__ = 'command_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_nick = Column(String(255), nullable=False, index=True)
    command = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    response_sent = Column(Boolean, default=False)


class BotSettings(Base):
    """Настройки бота"""
    __tablename__ = 'bot_settings'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


async def init_db():
    """Инициализация базы данных"""
    async with engine.begin() as conn:
        # Set PRAGMA для оптимизации SQLite
        from sqlalchemy import text
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.execute(text("PRAGMA synchronous=NORMAL"))
        
        # Создать таблицы
        await conn.run_sync(Base.metadata.create_all)
        
        # Добавить настройки по умолчанию
        default_settings = {
            "greetings_enabled": "true",
            "commands_enabled": "true",
            "log_commands": "true",
            "auto_delete_bot_messages": "true",
        }
        
        for key, value in default_settings.items():
            try:
                await conn.execute(
                    text("INSERT OR IGNORE INTO bot_settings (key, value) VALUES (:key, :value)"),
                    {"key": key, "value": value}
                )
            except:
                pass
    
    print("[ChatBot DB] Database initialized successfully")


@asynccontextmanager
async def get_db():
    """Получить сессию БД"""
    async with SessionLocal() as db:
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        finally:
            await db.close()


# Алиас для обратной совместимости
get_db_cm = get_db
