from fastapi import APIRouter, status, Depends, HTTPException
#from api.schema.schemas import HubSchema, UserSchema
from sqlalchemy.orm import Session
from core.config import get_db
from api.models import models
###############################################################
from api.schema.schemas import CreateGoogleRoads, CreateCollectedRoads, EditGoogleRoads, GeneralStatistics, StateStatistics
#from api.models.models import Road
from api.repository.roadsrepo import create_google_roads, road_already_uploaded,field_road_already_uploaded, create_field_roads, edit_google_data
from datetime import datetime
from sqlalchemy import func, asc

from shapely.geometry import MultiLineString, LineString, shape
from geoalchemy2 import WKBElement
from shapely import wkb, wkt


router = APIRouter(tags=['Roads'])


@router.post('/api/create_google_road')
async def create_google_road_data(road_data: CreateGoogleRoads, db:Session = Depends(get_db)):
    road_already_exist = road_already_uploaded(road_data.name, db)
    if road_already_exist:
        return {'Detail': "Road Already Created"}
    return create_google_roads(road_data, db)

@router.post('/api/create_field_data')
async def create_field_data(field_data: CreateCollectedRoads, db:Session= Depends(get_db)):
    field_data_exist = field_road_already_uploaded(field_data.name, db)
    if field_data_exist:
        return {'Detail': "Data Previously Collected"}
    return create_field_roads(field_data, db)
    #return {"Details": "Successfull"}


@router.get("/api/get_all_google_roads", status_code= status.HTTP_200_OK)
async def get_all_google_roads(state_name: str = None, region: str = None, cam_number: int=None,coverage: int=None,upload_status: str= None,col_start_date: datetime= None,col_end_date:datetime= None,upload_start_date:datetime=None, upload_end_date:datetime=None, skip: int=0, limit: int=170500, db:Session=Depends(get_db)):
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
        all_roads = all_roads.filter(models.Googleroads.collection_date >= col_start_date)
    if col_end_date:
        all_roads = all_roads.filter(models.Googleroads.collection_date <= col_end_date)
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
async def get_general_stats(db: Session= Depends(get_db)):
    """Returns general statistics about the Google Roads"""
    total_length_covered = db.query(func.sum(models.Googleroads.length * models.Googleroads.status / 100)).filter(models.Googleroads.status > 0).scalar() or 0.0
    total_kms = db.query(func.sum(models.Googleroads.length)).scalar() or 0.0
    
    total_file_uploaded= db.query(func.count(models.Googleroads.length)).filter(models.Googleroads.upload_status == "Uploaded").scalar() or 0.0
    total_upload_km = db.query(func.sum(models.Googleroads.length * models.Googleroads.status / 100)).filter(models.Googleroads.upload_status == "Uploaded").scalar() or 0.0
    
    cam1_km = db.query(func.sum(models.Googleroads.length * models.Googleroads.status / 100)).filter(models.Googleroads.status > 0, models.Googleroads.camera_number == 1).scalar() or 0.0
    
    cam2_km = db.query(func.sum(models.Googleroads.length * models.Googleroads.status / 100)).filter(models.Googleroads.status > 0, models.Googleroads.camera_number == 2).scalar() or 0.0
    
    cam3_km = db.query(func.sum(models.Googleroads.length * models.Googleroads.status / 100)).filter(models.Googleroads.status > 0, models.Googleroads.camera_number == 3).scalar() or 0.0
    
    cam4_km = db.query(func.sum(models.Googleroads.length * models.Googleroads.status / 100)).filter(models.Googleroads.status > 0, models.Googleroads.camera_number == 4).scalar() or 0.0
    
    cam5_km = db.query(func.sum(models.Googleroads.length * models.Googleroads.status / 100)).filter(models.Googleroads.status > 0, models.Googleroads.camera_number == 5).scalar() or 0.0
    return{
        "covered_km" : total_length_covered/1000,
        "percent_covered" : (total_length_covered/total_kms) * 100,
        'total_uploads': total_file_uploaded,
        'total_upload_km' : total_upload_km/1000,
        'cam1_km' : cam1_km/1000 if cam1_km!=0.0 else 0,
        'cam1_percent': (cam1_km/total_length_covered) *100 if cam1_km!=0.0 else 0,
        'cam2_km' : cam2_km/1000 if cam2_km!=0.0 else 0,
        'cam2_percent' :(cam2_km/total_length_covered) *100 if cam2_km!=0.0 else 0,
        'cam3_km' : cam3_km/1000 if cam3_km!=0.0 else 0,
        'cam3_percent': (cam3_km/total_length_covered) * 100 if cam3_km!=0.0 else 0,
        'cam4_km' : cam4_km/1000 if cam4_km!=0.0 else 0,
        'cam4_percent': (cam4_km/ total_length_covered) * 100 if cam4_km!=0.0 else 0,
        'cam5_km': cam5_km/1000 if cam5_km!=0.0 else 0,
        'cam5_percent': (cam5_km/total_length_covered) * 100 if cam5_km!=0.0 else 0
    }
    #123, 4,1
    
@router.get("/api/get_state_stats", response_model =StateStatistics, status_code= status.HTTP_200_OK)
async def get_state_statistics(db: Session= Depends(get_db)):
    oyo_covered = db.query(func.sum(models.Googleroads.length * models.Googleroads.status / 100)).filter(models.Googleroads.status > 0, models.Googleroads.state_name == "Oyo").scalar() or 0.0
    total_oyo = db.query(func.sum(models.Googleroads.length).filter(models.Googleroads.state_name=="Oyo")).scalar() or 0.0
    oyo_start_date = db.query(models.Googleroads.collection_date)\
                    .filter(models.Googleroads.status > 0, models.Googleroads.state_name == 'Oyo')\
                    .order_by(asc(models.Googleroads.collection_date))\
                    .first()
    oyo_starting = oyo_start_date[0] if oyo_start_date else "Not started yet"
    
    ogun_covered = db.query(func.sum(models.Googleroads.length * models.Googleroads.status / 100)).filter(models.Googleroads.status > 0, models.Googleroads.state_name == "Ogun").scalar() or 0.0
    total_ogun = db.query(func.sum(models.Googleroads.length).filter(models.Googleroads.state_name=="Ogun")).scalar() or 0.0
    ogun_start_date = db.query(models.Googleroads.collection_date)\
                    .filter(models.Googleroads.status > 0, models.Googleroads.state_name == 'Ogun')\
                    .order_by(asc(models.Googleroads.collection_date))\
                    .first()
    ogun_starting = ogun_start_date[0] if ogun_start_date else "Not started yet"
    
    lag_covered = db.query(func.sum(models.Googleroads.length * models.Googleroads.status / 100)).filter(models.Googleroads.status > 0, models.Googleroads.state_name == "Lagos").scalar() or 0.0
    total_lag = db.query(func.sum(models.Googleroads.length).filter(models.Googleroads.state_name=="Lagos")).scalar() or 0.0
    lag_start_date = db.query(models.Googleroads.collection_date)\
                    .filter(models.Googleroads.status > 0, models.Googleroads.state_name == 'Lagos')\
                    .order_by(asc(models.Googleroads.collection_date))\
                    .first()
    lag_starting = lag_start_date[0] if lag_start_date else "Not started yet"
    
    osun_covered = db.query(func.sum(models.Googleroads.length * models.Googleroads.status / 100)).filter(models.Googleroads.status > 0, models.Googleroads.state_name == "Osun").scalar() or 0.0
    total_osun = db.query(func.sum(models.Googleroads.length).filter(models.Googleroads.state_name=="Osun")).scalar() or 0.0
    osun_start_date = db.query(models.Googleroads.collection_date)\
                    .filter(models.Googleroads.status > 0, models.Googleroads.state_name == 'Osun')\
                    .order_by(asc(models.Googleroads.collection_date))\
                    .first()
    osun_starting = osun_start_date[0] if osun_start_date else "Not started yet"
    
    ondo_covered = db.query(func.sum(models.Googleroads.length * models.Googleroads.status / 100)).filter(models.Googleroads.status > 0, models.Googleroads.state_name == "Ondo").scalar() or 0.0
    total_ondo = db.query(func.sum(models.Googleroads.length).filter(models.Googleroads.state_name=="Ondo")).scalar() or 0.0
    ondo_start_date = db.query(models.Googleroads.collection_date)\
                    .filter(models.Googleroads.status > 0, models.Googleroads.state_name == 'Ondo')\
                    .order_by(asc(models.Googleroads.collection_date))\
                    .first()
    ondo_starting = ondo_start_date[0] if ondo_start_date else "Not started yet"
    
    edo_covered = db.query(func.sum(models.Googleroads.length * models.Googleroads.status / 100)).filter(models.Googleroads.status > 0, models.Googleroads.state_name == "Edo").scalar() or 0.0
    total_edo = db.query(func.sum(models.Googleroads.length).filter(models.Googleroads.state_name=="Edo")).scalar() or 0.0
    edo_start_date = db.query(models.Googleroads.collection_date)\
                    .filter(models.Googleroads.status > 0, models.Googleroads.state_name == 'Edo')\
                    .order_by(asc(models.Googleroads.collection_date))\
                    .first()
    edo_starting = edo_start_date[0] if edo_start_date else "Not started yet"
    
    delta_covered = db.query(func.sum(models.Googleroads.length * models.Googleroads.status / 100)).filter(models.Googleroads.status > 0, models.Googleroads.state_name == "Delta").scalar() or 0.0
    total_delta = db.query(func.sum(models.Googleroads.length).filter(models.Googleroads.state_name=="Delta")).scalar() or 0.0
    delta_start_date = db.query(models.Googleroads.collection_date)\
                    .filter(models.Googleroads.status > 0, models.Googleroads.state_name == 'Delta')\
                    .order_by(asc(models.Googleroads.collection_date))\
                    .first()
    delta_starting = delta_start_date[0] if delta_start_date else "Not started yet"
    return {
        "Oyo": oyo_covered/1000,
        "Oyo_percent": (oyo_covered/total_oyo) *100,
        "Oyo_start_date" : oyo_starting,
        "Ogun": ogun_covered/1000,
        "Ogun_percent" : (ogun_covered/total_ogun) * 100,
        "Ogun_start_date" : ogun_starting,
        "Lagos": lag_covered/1000, 
        "Lagos_percent": (lag_covered/total_lag) * 100,
        "Lagos_start_date" : lag_starting,
        "Osun": osun_covered/1000,
        "Osun_percent": (osun_covered/total_osun) * 100,
        "Osun_start_date" : osun_starting,
        "Ondo": ondo_covered/1000,
        "Ondo_percent": (ondo_covered/total_ondo) * 100,
        "Ondo_start_date" : ondo_starting,
        "Edo": edo_covered/1000,
        "Edo_percent": (edo_covered/total_edo) *100,
        "Edo_start_date" : edo_starting,
        "Delta": delta_covered/1000,
        "Delta_percent": (delta_covered/total_delta),
        "Delta_start_date" : delta_starting
    }
    
    