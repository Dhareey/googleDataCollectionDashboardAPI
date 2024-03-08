from sqlalchemy.orm import Session
from api.models import models
from api.schema.schemas import  GetCollectedRoad, CreateCollectedRoads, CreateGoogleRoads
from datetime import date


### Google 2024 road scope
### POST
##Verify Google Road Has Been uploaded Before
def road_already_uploaded(roadname: str, db:Session):
    """Check if a team is already registered"""
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
        geometry = road_geom
    )
    
    db.add(db_create_google_road_data)
    db.commit()
    db.refresh(db_create_google_road_data)
    return "Road added successfully"


def create_field_roads(request: CreateCollectedRoads, db:Session):
    try:
        road_geom = f"LINESTRING({', '.join([f'{x} {y}' for x, y in request.geometry])})"
    except:
        return {"Detail": "Invalid Coordinates"}
    db_create_field_data = models.collectedRoads(
        name = request.name,
        date = request.date,
        camera_number = request.camera_number,
        geometry = road_geom
    )
    
    db.add(db_create_field_data)
    db.commit()
    db.refresh(db_create_field_data)
    return "Collected Road Added Successfully"
## GET
