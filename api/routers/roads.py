from fastapi import APIRouter, status, Depends, HTTPException
#from api.schema.schemas import HubSchema, UserSchema
from sqlalchemy.orm import Session
from core.config import get_db
from api.models import models
###############################################################
#from api.schema.schemas import RoadCreateSchema, GetRoadSchema
#from api.models.models import Road
from api.repository.roadsrepo import create_google_roads

from shapely.geometry import MultiLineString, LineString, shape
from geoalchemy2 import WKBElement
from shapely import wkb, wkt

router = APIRouter(tags=['Roads'])
"""

@router.post("/api/create_road")
def create_line_string_data(road_data: RoadCreateSchema, db:Session = Depends(get_db)):
    return create_road(road_data, db)

@router.get("/api/get_roads", response_model=list[GetRoadSchema], status_code= status.HTTP_200_OK)
def get_road_data(skip: int=0, limit: int=100, db:Session=Depends(get_db)):
    roads = db.query(models.Road).offset(skip).limit(limit).all()
    for eachroad in roads:
        line = wkb.loads(bytes(eachroad.geometry.data))
        eachroad.geometry = [[point[0], point[1]] for point in line.coords]
    return roads

         """
    