from fastapi import APIRouter

from .roads import router
from .roads_2025 import router_2025

road_router = APIRouter()

road_router.include_router(router)
road_router.include_router(router_2025)