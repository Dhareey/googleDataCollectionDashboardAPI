from sqlalchemy.orm import Session
from api.models import models
from api.schema.schemas import  GetCollectedRoad, CreateCollectedRoads, CreateGoogleRoads, EditGoogleRoads, CreateGoogleJsonRoads
from fastapi import HTTPException
from datetime import date
from shapely.ops import unary_union


### Google 2024 road scope
### POST
##Verify Google Road Has Been uploaded Before
def road_already_uploaded(roadname: str, db:Session):
    """Check if a road is already uploaded"""
    existingroadName = db.query(models.Googleroads).filter(
        models.Googleroads.name == roadname).first()
    if existingroadName:
        return True
    return False

## Verify data sent from field team has been uploaded before
def field_road_already_uploaded(filename: str, db:Session):
    existingFileName = db.query(models.collectedRoads).filter(
        models.collectedRoads.name == filename).first()
    if existingFileName:
        return True
    return False


def create_google_roads(request: CreateGoogleRoads, db:Session):
    road_geom = f"LINESTRING({', '.join([f'{x} {y}' for x, y in request.geometry])})"
    
    
    stat = request.status if request.status is not None else 0
    camera_name = request.cam_name if request.cam_name else ""
    cam_num = request.camera_number if request.camera_number else 0
    col_date = request.collection_date if request.collection_date else date(2030, 1, 1)
    upload_stat = request.upload_status if request.upload_status else "Not Uploaded"
    uploadDate = request.upload_date if request.upload_date else date(2030, 1, 1)
    road_state = request.state_name if request.state_name else ""
    road_state_code = request.state_code if request.state_code else ""
    road_region = request.region if request.region else ""
    
    
    db_create_google_road_data = models.Googleroads(
        name = request.name,
        length= request.length,
        cam_name = camera_name,
        camera_number = cam_num,
        status = stat,
        collection_date = col_date,
        upload_status = upload_stat,
        upload_date = uploadDate,
        state_name = road_state,
        state_code = road_state_code,
        region = road_region,
        geometry = road_geom
    )
    
    db.add(db_create_google_road_data)
    db.commit()
    db.refresh(db_create_google_road_data)
    return "Road added successfully"


## PUT REQUESTS

def edit_google_data(road_id: str, request: EditGoogleRoads, db: Session):
    lookup_col = None
    if str(road_id).startswith("Road"):
        lookup_col = models.Googleroads.name
    elif str(id).startswith('VID'):
        lookup_col = models.Googleroads.cam_name
    else:
        lookup_col = models.Googleroads.id
        
    existing_road = db.query(models.Googleroads).filter(lookup_col == road_id).first()
    if existing_road is None:
        raise HTTPException(status_code = 404, detail= "Road not found")
    
    if request.name != None:
        existing_road.name = request.name
    if request.length != None:
        existing_road.length  = request.length
    if request.cam_name != None:
        existing_road.cam_name = request.cam_name
    if request.camera_number != None:
        existing_road.camera_number = request.camera_number
    if request.status != None:
        existing_road.status = request.status
    if request.collection_date != None:
        existing_road.collection_date = request.collection_date
    if request.upload_status != None:
        existing_road.upload_status = request.upload_status
    if request.upload_date != None:
        existing_road.upload_date = request.upload_date
    if request.state_name != None:
        existing_road.state_name = request.state_name
    if request.state_code != None:
        existing_road.state_code = request.state_code
    if request.region != None:
        existing_road.region = request.region
    db.commit()
    return "Update Successfull"

def json_road_already_uploaded(roadname: str, db:Session):
    """Check if a road is already uploaded"""
    existingroadName = db.query(models.Google_Roads_Json).filter(
        models.Google_Roads_Json.name == roadname).first()
    if existingroadName:
        return True
    return False


def create_google_json_roads(request: CreateGoogleJsonRoads , db:Session):
    road = models.Google_Roads_Json(**request.dict())
    db.add(road)
    db.commit()
    db.refresh(road)
    return road


