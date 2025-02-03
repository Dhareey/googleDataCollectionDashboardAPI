from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
import os
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy.orm import sessionmaker

env_dir = Path(__file__).resolve().parent.parent

env_file = env_dir / '.env'

load_dotenv(dotenv_path=env_file)

# Class to get the postgresql details


class Settings:
    PROJECT_NAME: str = "Google Street View App"
    PROJEVT_VERSION: str = "1.0.0"

    POSTGRES_USER: str = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", 'localhost')
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", 5432)
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "tdd")
    RENDER_DB_URL: str= os.getenv("DB_URL")
    RENDER_POSTGRES_USER: str= os.getenv("RENDER_POSTGRES_USER")
    RENDER_POSTGRES_PASSWORD: str= os.getenv("RENDER_PASSWORD")
    RENDER_POSTGRES_SERVER: str= os.getenv("RENDER_SERVER")
    RENDER_DB: str=os.getenv("RENDER_DB")
    AWS_URL: str= os.getenv("AWS_DB")

    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}/{POSTGRES_DB}"
    DATABASE_URL_ASYNC = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}/{POSTGRES_DB}"
    #DATABASE_URL = f"{AWS_URL}"
    #DATABASE_URL = f"{AWS_URL}"
    #DATABASE_URL = f"{RENDER_DB_URL}"
    
    #DATABASE_URL= f"postgresql://{RENDER_POSTGRES_USER}:{RENDER_POSTGRES_PASSWORD}@{RENDER_POSTGRES_SERVER}/{RENDER_DB}"
    #DATABASE_URL_ASYNC= f"postgresql+asyncpg://{RENDER_POSTGRES_USER}:{RENDER_POSTGRES_PASSWORD}@{RENDER_POSTGRES_SERVER}/{RENDER_DB}"


settings = Settings()

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
ASYNC_DATABASE_URL = settings.DATABASE_URL_ASYNC

engine = create_engine(SQLALCHEMY_DATABASE_URL)

metadata = MetaData()

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

Base = declarative_base()

########################################
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)

# Create a sessionmaker factory for async sessions
async_session = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base for declaring models
#async_base = declarative_base()

# Dependency to provide a session
async def get_async_session() -> AsyncSession:
    async with async_session() as session:
        yield session
