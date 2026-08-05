from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Declarative base — every module's ORM models inherit from this."""


def create_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(settings.database_url, echo=settings.debug, pool_pre_ping=True)


engine = create_engine()
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
