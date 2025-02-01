from fastapi import APIRouter, status, Depends, HTTPException, BackgroundTasks, Query
#from api.schema.schemas import HubSchema, UserSchema
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import get_db
from api.models.models import Hubs2025, Roads2025
from core.database import get_async_session
###############################################################
from api.schema.schemas import (
    CreateGoogleRoads, 
    CreateCollectedRoads, 
    EditGoogleRoads, 
    GeneralStatistics, 
    StateStatistics, 
    CreateGoogleJsonRoads, 
    EditGoogleJsonRoads, 
    CameraCoverageSchema,
    Hubs2025Response,
    PaginationResponse,
    PaginationRoadResponse,
    CurrentStateResponse
)
from typing import Optional
from sqlalchemy.future import select
#from api.models.models import Road
from api.repository.roadsrepo import create_google_roads, road_already_uploaded, edit_google_data, json_road_already_uploaded, create_google_json_roads
from datetime import datetime, date
from sqlalchemy import func, case, and_

from shapely.geometry import MultiLineString, LineString, shape
from geoalchemy2 import WKBElement
from shapely import wkb
from typing import List
from api.models.models import Google_Roads_Json
from api.models import models
from api.tasks.tasks import update_camera_coverage_background

router_2025 = APIRouter(tags=['Roads_2025'])