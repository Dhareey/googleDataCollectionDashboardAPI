from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
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
    DB_URL: str= os.getenv("DB_URL")

    #DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}/{POSTGRES_DB}"
    DATABASE_URL = "postgresql://postgres:shadie77@54.226.124.34:5432/fastapiDB"

    
    #DATABASE_URL= "postgres://dhareey:H72Sg9z1JLP24RChvHDKVgghgMorVEqt@dpg-cod80520si5c738qqdqg-a.oregon-postgres.render.com/googlestreetview"


settings = Settings()

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)

metadata = MetaData()

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

Base = declarative_base()
