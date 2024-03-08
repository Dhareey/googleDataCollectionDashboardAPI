from fastapi import APIRouter, status, Depends, HTTPException
#from api.schema.schemas import HubSchema, UserSchema
from sqlalchemy.orm import Session
from core.config import get_db
from api.models import models
###############################################################
from api.schema.schemas import CreateGoogleRoads, CreateCollectedRoads, EditGoogleRoads
#from api.models.models import Road
from api.repository.roadsrepo import create_google_roads, road_already_uploaded,field_road_already_uploaded, create_field_roads, edit_google_data
from datetime import datetime

from shapely.geometry import MultiLineString, LineString, shape
from geoalchemy2 import WKBElement
from shapely import wkb, wkt

router = APIRouter(tags=['Roads'])


@router.post('/api/create_google_road')
def create_google_road_data(road_data: CreateGoogleRoads, db:Session = Depends(get_db)):
    road_already_exist = road_already_uploaded(road_data.name, db)
    if road_already_exist:
        return {'Detail': "Road Already Created"}
    return create_google_roads(road_data, db)

@router.post('/api/create_field_data')
def create_field_data(field_data: CreateCollectedRoads, db:Session= Depends(get_db)):
    field_data_exist = field_road_already_uploaded(field_data.name, db)
    if field_data_exist:
        return {'Detail': "Data Previously Collected"}
    return create_field_roads(field_data, db)


@router.get("/api/get_all_google_roads", status_code= status.HTTP_200_OK)
def get_all_google_roads(state_name: str = None, cam_number: int=None,coverage: int=None,upload_status: str= None,col_start_date: datetime= None,col_end_date:datetime= None,upload_start_date:datetime=None, upload_end_date:datetime=None, skip: int=0, limit: int=10000, db:Session=Depends(get_db)):
    all_roads = db.query(models.Googleroads)
    if state_name:
        all_roads = all_roads.filter(models.Googleroads.state_name == state_name)
    if cam_number:
        all_roads = all_roads.filter(models.Googleroads.camera_number == cam_number)
    if coverage:
        all_roads = all_roads.filter(models.Googleroads.status >= coverage)
    if upload_status:
        all_roads = all_roads.filter(models.Googleroads.upload_status == upload_status)
    if col_start_date:
        all_roads = all_roads.filter(models.Googleroads.collection_date >= col_start_date)
    if col_end_date:
        all_roads = all_roads.filter(models.Googleroads.collection_date <= col_end_date)
    if upload_start_date:
        all_roads = all_roads.filter(models.Googleroads.upload_date >= upload_start_date)
    if upload_end_date:
        all_roads = all_roads.filter(models.Googleroads.upload_date <= upload_end_date)
    
        
    roads = all_roads.offset(skip).limit(limit).all()
    for eachroad in roads:
        line = wkb.loads(bytes(eachroad.geometry.data))
        eachroad.geometry = [[point[0], point[1]] for point in line.coords]
    return roads

@router.get("/api/get_google_road", status_code = status.HTTP_200_OK)
def get_one_road(id : str, db:Session=Depends(get_db)):
    lookup_col = None
    if str(id).startswith('Road'):
        lookup_col = models.Googleroads.name
    elif str(id).startswith('VID'):
        lookup_col = models.Googleroads.cam_name
    else:
        lookup_col = models.Googleroads.id
        
    road = db.query(models.Googleroads).filter(lookup_col == id).first()
    if road is None:
        raise HTTPException(status_code=404, detail="Road not found")
    line = wkb.loads(bytes(road.geometry.data))
    road.geometry = [[point[0], point[1]] for point in line.coords]
    return road

@router.put("/api/update_google_road/{road_id}", status_code = status.HTTP_200_OK)
def update_google_road(road_id: str, updated_road: EditGoogleRoads, db: Session= Depends(get_db)):
    return edit_google_data(road_id, updated_road, db)
    
    # Update the road attributes with the provided data
    
        
    #db.commit()
    #db.refresh(existing_road)
    #return existing_road
    return "Done"


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
    