from sqlalchemy.orm import Session
from api.models import models
from api.schema.schemas import  GetCollectedRoad, CreateCollectedRoads, CreateGoogleRoads
from shapely.geometry import LineString


### Google 2024 road scope
### POST
def create_google_roads(request: CreateGoogleRoads, db:Session):
    road_geom = f"LINESTRING({', '.join([f'{x} {y}' for x, y in request.geometry])})"
    
    db_create_google_road_data = models.Road(
        name = request.name,
        length= request.length,
        geometry = road_geom
    )
    
    db.add(db_create_google_road_data)
    db.commit()
    db.refresh(db_create_google_road_data)
    return "Road added successfully"


## GET
