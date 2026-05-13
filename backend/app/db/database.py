from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.config import settings
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

# --- Асинхронная часть (для FastAPI) ---
async_engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# --- Синхронная часть (для Celery) ---
SYNC_DATABASE_URL = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
sync_engine = create_engine(SYNC_DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Зависимость для API (остается без изменений)
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Функция для воркера
def get_sync_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()