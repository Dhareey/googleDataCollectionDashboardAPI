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
    EditGoogleRoads, 
    GeneralStatistics,  
    CreateGoogleJsonRoads, 
    EditGoogleJsonRoads, 
    CameraCoverageSchema,
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
from datetime import datetime, timedelta


router = APIRouter(tags=['Roads'])

# Pagination helper
def paginate(query, page: int, page_size: int):
    return query.limit(page_size).offset((page - 1) * page_size)


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

#################################################################################

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

@router.put('/api/edit_google_road_json/{road_name}')
async def edit_google_road_json(road_name: str, road_data: EditGoogleJsonRoads, background_tasks:BackgroundTasks, db: Session = Depends(get_db)):
    road = db.query(models.Google_Roads_Json).filter(models.Google_Roads_Json.name == road_name).first()
    road_length = road.length
    road_col_date = road.collection_date
    if not road:
        raise HTTPException(status_code=404, detail="Road not found")
    
    # Convert Pydantic model to dictionary
    update_data = road_data.dict(exclude_unset=True)
    
    # Update the road data
    for key, value in update_data.items():
        setattr(road, key, value)
    
    db.commit()
    print(road_col_date)
    if road_col_date == datetime.strptime("2030-01-01", "%Y-%m-%d").date():
        background_tasks.add_task(update_camera_coverage_background, road_data.collection_date, road_data.camera_number, road_length, db)
    return {"message": "Road updated successfully"}

@router.get('/api/google_road_stats')
async def get_google_road_stats(
    state_name: str, 
    start_date: date = None, 
    end_date: date = None, 
    db: Session = Depends(get_db)
):
    # Start with the base query to get total length of roads for the given state name
    total_length_query = db.query(func.sum(Google_Roads_Json.length)).filter(
        Google_Roads_Json.state_name == state_name
    )


    # Execute the query to get total length
    total_length = total_length_query.scalar() or 0  # Use scalar() to get the value, or default to 0 if no result

    # Now, get other statistics
    query = db.query(
        func.sum(Google_Roads_Json.length).filter(Google_Roads_Json.status == 100),  # Total length where status is 100
        func.min(Google_Roads_Json.collection_date).filter(Google_Roads_Json.status == 100)  # First date where status is 100
    ).filter(
        Google_Roads_Json.state_name == state_name
    )

    # Add filtering by collection date if start_date and end_date are provided
    if start_date and end_date:
        query = query.filter(
            Google_Roads_Json.collection_date >= start_date,
            Google_Roads_Json.collection_date <= end_date
        )

    # Execute the query
    total_length_status_100, first_date_status_100 = query.first()

    # Calculate the percentage covered by roads where status is 100
    percentage_covered = (total_length_status_100 / total_length) * 100 if total_length and total_length_status_100 else 0
    
    return {
        "state_name": state_name,
        "total_length": round(total_length/1000,2) if total_length else 0,
        "total_length_status_100": round(total_length_status_100/1000,2) if total_length_status_100 else 0,
        "first_date_status_100": first_date_status_100 if first_date_status_100 else "Not started yet",
        "percentage_covered": round(percentage_covered, 2)
    }    
    
@router.get('/api/stats_camera')
async def get_camera_stats(
    camera_number: int, 
    start_date: date = None, 
    end_date: date = None, 
    db: Session = Depends(get_db)
):
    # Start with the base query
    query = db.query(
        func.sum(Google_Roads_Json.length),  # Total length of all roads where status is 100
        func.sum(case((Google_Roads_Json.camera_number == camera_number, Google_Roads_Json.length), else_=0)),  # Length of roads with status 100 and matching camera number
    ).filter(
        Google_Roads_Json.status == 100
    )

    # Add filtering by collection date if start_date and end_date are provided
    if start_date and end_date:
        query = query.filter(
            Google_Roads_Json.collection_date >= start_date,
            Google_Roads_Json.collection_date <= end_date
        )

    # Execute the query
    stats = query.first()

    total_length_status_100, length_with_camera_number = stats
    
    if total_length_status_100 is None:
        total_length_status_100 = 0
    
    if length_with_camera_number is None:
        length_with_camera_number = 0

    # Calculate the percentage covered by the camera
    percentage_covered = (length_with_camera_number / total_length_status_100) * 100 if total_length_status_100 != 0 else 0
    
    return {
        "camera_number": camera_number,
        "length_with_camera_number": round(length_with_camera_number/1000,2),
        "percentage_covered": round(percentage_covered, 2)
    }
    
@router.get("/api/get_progress")
async def get_road_length_stats( 
    start_date: date = None, 
    end_date: date = None,
    db: Session = Depends(get_db)):
    # Get the sum of the length of roads where road_status is 100
    sum_length_status_100 = db.query(func.sum(Google_Roads_Json.length)).filter(Google_Roads_Json.status == 100).scalar() or 0
    
    # Get the total length of all roads
    total_length_all_roads = db.query(func.sum(Google_Roads_Json.length)).scalar() or 0
    if start_date and end_date:
        sum_length_status_100 = db.query(func.sum(Google_Roads_Json.length)).filter(
            Google_Roads_Json.status == 100,
            Google_Roads_Json.collection_date >= start_date,
            Google_Roads_Json.collection_date <= end_date
        ).scalar() or 0

    # Calculate the percentage
    percentage = (sum_length_status_100 / total_length_all_roads) * 100 if total_length_all_roads != 0 else 0
    
    return {
        "total_covered_2024": round(sum_length_status_100 / 1000, 2),
        "total_road_2024": round(total_length_all_roads / 1000, 2),
        "percentage_2024": round(percentage, 2),
        "total_covered_2023": 5727.76,
        "total_road_2023": 56513.61,
        "percentage_2023": round((5727.76 / 56513.61) * 100, 2),
    }
    
    
@router.get('/api/get_daily_data', response_model=List[CameraCoverageSchema])
async def get_daily_data(
    start_date: date = None, 
    end_date: date = None,
    db:Session=Depends(get_db)):
    query = db.query(models.CameraCoverage)
    
    if start_date and end_date:
        query = query.filter(and_(models.CameraCoverage.date >= start_date, models.CameraCoverage.date <= end_date))
    elif start_date:
        query = query.filter(models.CameraCoverage.date >= start_date)
    elif end_date:
        query = query.filter(models.CameraCoverage.date <= end_date)
    
    camera_coverages = query.all()
    return camera_coverages

