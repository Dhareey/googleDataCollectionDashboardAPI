from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.models import models
from core.database import engine
from api.routers import roads


app = FastAPI()

models.Base.metadata.create_all(engine)

# Configure CORS. Remove later
"""
origins = [
    'exp://192.168.100.65:8081',
    'http://192.168.100.65:8081',
]
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(roads.router)
#ngrok http 8000