import json
import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker, load_only

from api.models.models import Roads2025
from api.models.models import Currentstate  # Replace with your actual model import
from core.database import Base  # Replace with your database setup
from api.controllers.enum import StateNameEnum, RegionEnum  # Replace with your actual Enum imports

# Database connection
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
#DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}/{POSTGRES_DB}"  # Update with your connection string
DATABASE_URL= f"postgresql+psycopg2://{RENDER_POSTGRES_USER}:{RENDER_POSTGRES_PASSWORD}@{RENDER_POSTGRES_SERVER}/{RENDER_DB}"
engine = create_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(bind=engine)

BATCH_SIZE = 1000

region_mapping = {
    'SEZ': RegionEnum.SOUTH_EAST,
    'NEZ': RegionEnum.NORTH_EAST,
    'SSZ': RegionEnum.SOUTH_SOUTH,
    'NCZ': RegionEnum.NORTH_CENTRAL,
    'SWZ': RegionEnum.SOUTH_WEST,
    'NWZ': RegionEnum.NORTH_WEST
}

# Create a dictionary mapping state names to enum members
state_mapping = {member.value: member for member in StateNameEnum}


async def seed_hubs(file_path):
    # Load data from JSON file
    with open(file_path, "r") as f:
        roads_data = json.load(f)
        
    # Prepare mappings for bulk insert
    mappings = [
        {
            "name": road['Name'],
            "length": road["length"],
            "region": region_mapping[road["region"]],
            "state_name": state_mapping[road["state"]],
            "scope_name": "2025_Scope",
            "hub_id": road["hub_id"],
            "geometry": road["Geometry"][0]
        }
        for road in roads_data
    ]

    with async_session() as session:
        for i in range(0, len(mappings), BATCH_SIZE):
            batch = mappings[i:i + BATCH_SIZE]
            session.bulk_insert_mappings(Roads2025, batch)
            session.commit()
            print(f"Inserted batch {i // BATCH_SIZE + 1}")

if __name__ == "__main__":
    asyncio.run(seed_hubs("./new_roads2.json"))