from fastapi import APIRouter, status, Depends, HTTPException
#from api.schema.schemas import HubSchema, UserSchema
from sqlalchemy.orm import Session
from core.config import get_db
from api.models import models
###############################################################
from api.schema.schemas import CreateGoogleRoads, CreateCollectedRoads, EditGoogleRoads, GeneralStatistics, StateStatistics, CreateGoogleJsonRoads
#from api.models.models import Road
from api.repository.roadsrepo import create_google_roads, road_already_uploaded, edit_google_data, json_road_already_uploaded, create_google_json_roads
from datetime import datetime
from sqlalchemy import func

from shapely.geometry import MultiLineString, LineString, shape
from geoalchemy2 import WKBElement
from shapely import wkb
from typing import List


router = APIRouter(tags=['Roads'])


@router.post('/api/create_google_road')
async def create_google_road_data(road_data: CreateGoogleRoads, db:Session = Depends(get_db)):
    road_already_exist = road_already_uploaded(road_data.name, db)
    if road_already_exist:
        return {'Detail': "Road Already Created"}
    return create_google_roads(road_data, db)


@router.get("/api/get_all_google_roads", status_code= status.HTTP_200_OK)
async def get_all_google_roads(state_name: str = None, region: str = None, cam_number: int=None,coverage: int=None,upload_status: str= None,col_start_date: str= None,col_end_date:str= None,upload_start_date:datetime=None, upload_end_date:datetime=None, skip: int=0, limit: int=170500, db:Session=Depends(get_db)):
    all_roads = db.query(models.Googleroads)
    if state_name:
        all_roads = all_roads.filter(models.Googleroads.state_name == state_name)
    if region:
        all_roads = all_roads.filter(models.Googleroads.region == region)
    if cam_number:
        all_roads = all_roads.filter(models.Googleroads.camera_number == cam_number)
    if coverage:
        all_roads = all_roads.filter(models.Googleroads.status >= coverage)
    if upload_status:
        all_roads = all_roads.filter(models.Googleroads.upload_status == upload_status)
    if col_start_date:
        try:
            start = datetime.strptime(col_start_date, "%Y-%m-%d").date()
            all_roads = all_roads.filter(models.Googleroads.collection_date >= start)
        except:
            return {
                "Error": "Invalid Start Date"
            }
    if col_end_date:
        try:
            end = datetime.strptime(col_end_date, "%Y-%m-%d").date()
            all_roads = all_roads.filter(models.Googleroads.collection_date <= end)
        except:
            return{
                "Error": "Invalid End Date"
            }
    if upload_start_date:
        all_roads = all_roads.filter(models.Googleroads.upload_date >= upload_start_date)
    if upload_end_date:
        all_roads = all_roads.filter(models.Googleroads.upload_date <= upload_end_date)
    
    all_roads = all_roads.order_by(models.Googleroads.id)
    roads = all_roads.offset(skip).limit(limit).all()
    for eachroad in roads:
        line = wkb.loads(bytes(eachroad.geometry.data))
        eachroad.geometry = [[point[0], point[1]] for point in line.coords]
    return roads

@router.get("/api/get_google_road", status_code = status.HTTP_200_OK)
async def get_one_road(id : str, db:Session=Depends(get_db)):
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
async def update_google_road(road_id: str, updated_road: EditGoogleRoads, db: Session= Depends(get_db)):
    return edit_google_data(road_id, updated_road, db)
    
    # Update the road attributes with the provided data
    
        
    #db.commit()
    #db.refresh(existing_road)
    #return existing_road
    return "Done"

@router.get("/api/get_stats", response_model =GeneralStatistics, status_code= status.HTTP_200_OK)
async def get_general_stats(db: Session = Depends(get_db), col_start_date: str = None, col_end_date: str = None):
    all_roads = db.query(models.Googleroads)  # Initialize queryset with all data
    
    if col_start_date:
        try:
            start = datetime.strptime(col_start_date, "%Y-%m-%d").date()
            all_roads = all_roads.filter(models.Googleroads.collection_date >= start)
        except:
            return {
                "Error": "Invalid Start Date"
            }
    if col_end_date:
        try:
            end = datetime.strptime(col_end_date, "%Y-%m-%d").date()
            all_roads = all_roads.filter(models.Googleroads.collection_date <= end)
        except:
            return{
                "Error": "Invalid End Date"
            }

    """Returns general statistics about the Google Roads"""
    total_length_covered = all_roads.filter(models.Googleroads.status > 0).with_entities(func.sum(models.Googleroads.length * models.Googleroads.status / 100)).scalar() or 0.0
    total_kms = all_roads.with_entities(func.sum(models.Googleroads.length)).scalar() or 0.0
    
    total_file_uploaded = all_roads.filter(models.Googleroads.upload_status == "Uploaded").with_entities(func.count(models.Googleroads.length)).scalar() or 0.0
    total_upload_km = all_roads.filter(models.Googleroads.upload_status == "Uploaded").with_entities(func.sum(models.Googleroads.length * models.Googleroads.status / 100)).scalar() or 0.0
    
    cam1_km = all_roads.filter(models.Googleroads.status > 0, models.Googleroads.camera_number == 1).with_entities(func.sum(models.Googleroads.length * models.Googleroads.status / 100)).scalar() or 0.0
    cam2_km = all_roads.filter(models.Googleroads.status > 0, models.Googleroads.camera_number == 2).with_entities(func.sum(models.Googleroads.length * models.Googleroads.status / 100)).scalar() or 0.0
    cam3_km = all_roads.filter(models.Googleroads.status > 0, models.Googleroads.camera_number == 3).with_entities(func.sum(models.Googleroads.length * models.Googleroads.status / 100)).scalar() or 0.0
    cam4_km = all_roads.filter(models.Googleroads.status > 0, models.Googleroads.camera_number == 4).with_entities(func.sum(models.Googleroads.length * models.Googleroads.status / 100)).scalar() or 0.0
    cam5_km = all_roads.filter(models.Googleroads.status > 0, models.Googleroads.camera_number == 5).with_entities(func.sum(models.Googleroads.length * models.Googleroads.status / 100)).scalar() or 0.0
    cam6_km = all_roads.filter(models.Googleroads.status > 0, models.Googleroads.camera_number == 6).with_entities(func.sum(models.Googleroads.length * models.Googleroads.status / 100)).scalar() or 0.0
    
    return {
        "covered_km": total_length_covered / 1000,
        "percent_covered": (total_length_covered / total_kms) * 100 if total_kms else 0,
        'total_uploads': total_file_uploaded,
        'total_upload_km': total_upload_km / 1000,
        'cam1_km': cam1_km / 1000 if cam1_km != 0.0 else 0,
        'cam1_percent': (cam1_km / total_length_covered) * 100 if total_length_covered != 0.0 else 0,
        'cam2_km': cam2_km / 1000 if cam2_km != 0.0 else 0,
        'cam2_percent': (cam2_km / total_length_covered) * 100 if total_length_covered != 0.0 else 0,
        'cam3_km': cam3_km / 1000 if cam3_km != 0.0 else 0,
        'cam3_percent': (cam3_km / total_length_covered) * 100 if total_length_covered != 0.0 else 0,
        'cam4_km': cam4_km / 1000 if cam4_km != 0.0 else 0,
        'cam4_percent': (cam4_km / total_length_covered) * 100 if total_length_covered != 0.0 else 0,
        'cam5_km': cam5_km / 1000 if cam5_km != 0.0 else 0,
        'cam5_percent': (cam5_km / total_length_covered) * 100 if total_length_covered != 0.0 else 0,
        'cam6_km': cam6_km / 1000 if cam6_km != 0.0 else 0,
        'cam6_percent': (cam6_km / total_length_covered) * 100 if total_length_covered != 0.0 else 0
    }

    #123, 4,1
    
@router.get("/api/get_state_stats", status_code= status.HTTP_200_OK)
async def get_state_statistics(db: Session=Depends(get_db), col_start_date: str=None, col_end_date: str=None):
    all_roads = db.query(models.Googleroads)  # Initialize queryset with all data
    
    if col_start_date:
        try:
            start = datetime.strptime(col_start_date, "%Y-%m-%d").date()
            all_roads = all_roads.filter(models.Googleroads.collection_date >= start)
        except:
            return {
                "Error": "Invalid Start Date"
            }
    if col_end_date:
        try:
            end = datetime.strptime(col_end_date, "%Y-%m-%d").date()
            all_roads = all_roads.filter(models.Googleroads.collection_date <= end)
        except:
            return {
                "Error": "Invalid End Date"
            }
            
    def calculate_state_statistics(state_name):
        total_length_covered = all_roads.filter(models.Googleroads.state_name == state_name, models.Googleroads.status > 0).with_entities(func.sum(models.Googleroads.length * models.Googleroads.status / 100)).scalar() or 0.0
        total_length = all_roads.filter(models.Googleroads.state_name == state_name).with_entities(func.sum(models.Googleroads.length)).scalar() or 0.0
        start_date = all_roads.filter(models.Googleroads.state_name == state_name, models.Googleroads.status > 0).with_entities(func.min(models.Googleroads.collection_date)).scalar()
        starting = start_date if start_date else "Not started yet"
        return {
            "covered_km": round(total_length_covered / 1000, 2),
            "percent_covered": round((total_length_covered / total_length) * 100, 2) if total_length else 0,
            "start_date": starting
        }

    oyo_stats = calculate_state_statistics("Oyo")
    ogun_stats = calculate_state_statistics("Ogun")
    lagos_stats = calculate_state_statistics("Lagos")
    osun_stats = calculate_state_statistics("Osun")
    ondo_stats = calculate_state_statistics("Ondo")
    edo_stats = calculate_state_statistics("Edo")
    delta_stats = calculate_state_statistics("Delta")

    return {
        "Oyo": oyo_stats,
        "Ogun": ogun_stats,
        "Lagos": lagos_stats,
        "Osun": osun_stats,
        "Ondo": ondo_stats,
        "Edo": edo_stats,
        "Delta": delta_stats
    }

 

@router.post('/api/create_google_road_json')
async def create_google_json_road_data(road_data: CreateGoogleJsonRoads, db:Session = Depends(get_db)):
    road_already_exist = json_road_already_uploaded(road_data.name, db)
    if road_already_exist:
        return {'Detail': "Road Already Created"}
    return create_google_json_roads(road_data, db)

@router.get('/api/get_all_google_json_roads', response_model=List[CreateGoogleJsonRoads])
async def get_all_google_json_roads(state_name: str = None, region: str = None, cam_number: int=None,coverage: int=None,upload_status: str= None,col_start_date: str= None,col_end_date:str= None,upload_start_date:datetime=None, upload_end_date:datetime=None, skip: int=0, limit: int=220000,db: Session = Depends(get_db)):
    all_roads = db.query(models.Google_Roads_Json)
    if state_name:
        all_roads = all_roads.filter(models.Google_Roads_Json.state_name == state_name)
    if region:
        all_roads = all_roads.filter(models.Google_Roads_Json.region == region)
    if cam_number:
        all_roads = all_roads.filter(models.Google_Roads_Json.camera_number == cam_number)
    if coverage:
        all_roads = all_roads.filter(models.Google_Roads_Json.status >= coverage)
    if upload_status:
        all_roads = all_roads.filter(models.Google_Roads_Json.upload_status == upload_status)
    if col_start_date:
        try:
            start = datetime.strptime(col_start_date, "%Y-%m-%d").date()
            all_roads = all_roads.filter(models.Google_Roads_Json.collection_date >= start)
        except:
            return {
                "Error": "Invalid Start Date"
            }
    if col_end_date:
        try:
            end = datetime.strptime(col_end_date, "%Y-%m-%d").date()
            all_roads = all_roads.filter(models.Google_Roads_Json.collection_date <= end)
        except:
            return{
                "Error": "Invalid End Date"
            }
    if upload_start_date:
        all_roads = all_roads.filter(models.Google_Roads_Json.upload_date >= upload_start_date)
    if upload_end_date:
        all_roads = all_roads.filter(models.Google_Roads_Json.upload_date <= upload_end_date)
    
    all_roads = all_roads.order_by(models.Google_Roads_Json.id)
    roads = all_roads.offset(skip).limit(limit).all()
    return roads