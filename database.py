# database.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database connection string from environment variables
# Example: postgresql+asyncpg://user:password@host:port/database_name
# For Supabase, this would be found in your project settings -> Database -> Connection String
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres")

# Create an asynchronous SQLAlchemy engine
# pool_pre_ping=True helps maintain healthy connections
# future=True enables SQLAlchemy 2.0 style usage
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, future=True, echo=False)

# Create an asynchronous sessionmaker for database interactions
# expire_on_commit=False prevents objects from expiring after commit,
# which can be useful when working with objects after they've been committed.
AsyncSessionLocal = async_sessionmaker(engine, autocommit=False, autoflush=False, expire_on_commit=False, class_=AsyncSession)

# Base class for declarative models
Base = declarative_base()

async def get_db():
    """
    FastAPI dependency to get an asynchronous database session.
    Yields a session that is automatically closed after the request.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
