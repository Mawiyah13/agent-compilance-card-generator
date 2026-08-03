import pytest
import socket
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import app.core.database as database

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Fast TCP socket check to verify if PostgreSQL port is open/reachable
    postgres_up = False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        s.connect((settings.POSTGRES_SERVER, settings.POSTGRES_PORT))
        postgres_up = True
        s.close()
    except Exception:
        pass

    if postgres_up:
        # Recreate engine with NullPool for tests to avoid closed event loop issues in Windows/asyncpg
        test_engine = create_async_engine(
            settings.SQLALCHEMY_ASYNC_DATABASE_URI,
            poolclass=NullPool,
            echo=False
        )
        database.async_engine = test_engine
        database.AsyncSessionLocal = async_sessionmaker(
            bind=test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
    else:
        # Fallback to local SQLite database for test execution when Postgres is unreachable
        sqlite_async_uri = "sqlite+aiosqlite:///./test_compliance_db.sqlite"
        sqlite_sync_uri = "sqlite:///./test_compliance_db.sqlite"
        
        database.async_engine = create_async_engine(sqlite_async_uri, echo=False)
        database.AsyncSessionLocal = async_sessionmaker(
            bind=database.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
        database.engine = create_engine(sqlite_sync_uri, echo=False)
        database.SessionLocal = sessionmaker(
            bind=database.engine,
            autocommit=False,
            autoflush=False
        )

    # Create all tables on the configured test database
    import asyncio
    from app.models import Base
    async def create_tables():
        async with database.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    try:
        asyncio.run(create_tables())
    except Exception:
        pass

