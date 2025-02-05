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
    HubNamesResponse,
    UpdateRoadRequest,
    StatesResponse,
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
        
    return camera_coverages

####################################################################################################
###2025 ENDPOINTS

# GET all 2025 Hubs with pagination
@router.get("/hubs_2025", response_model=list[Hubs2025Response])
async def get_all_hubs(
    page: int = Query(1, ge=1),  # Default page = 1
    session: AsyncSession = Depends(get_async_session),
):
    query = select(Hubs2025)
    paginated_query = paginate(query, page, 1000)  # 1000 rows per page
    result = await session.execute(paginated_query)
    return result.scalars().all()

@router.get("/api/hubs", status_code=status.HTTP_200_OK, response_model=PaginationResponse)
async def get_all_2005_hubs(
    page: int = Query(1, ge=1),  # Default page is 1, and must be greater than or equal to 1
    limit: int = Query(1000, le=1000),  # Default limit is 10, maximum limit is 100
    db: Session = Depends(get_db)
):
    # Calculate offset for pagination
    offset = (page - 1) * limit

    # Query the database with offset and limit
    query = db.query(Hubs2025)
    
    # Get the total count of hubs
    total_count = query.count()

    # Query the data for the current page
    hubs = query.offset(offset).limit(limit).all()

    # Calculate next and previous pages
    next_page = page + 1 if offset + limit < total_count else None
    previous_page = page - 1 if page > 1 else None

    return {
        "count": total_count,
        "next": next_page,
        "previous": previous_page,
        "results": hubs,
    }
    
@router.get("/api/roads_2025", status_code=status.HTTP_200_OK, response_model=PaginationRoadResponse)
async def get_all_2005_hubs(
    state_name: Optional[str] = None,
    region: Optional[str] = None,
    assigned_cam_number: Optional[int] = None,
    camera_number: Optional[int] = None,
    status: Optional[int] = None,
    collected_date: Optional[str] = None,  # If using ISO 8601 format
    hub_id: Optional[int] = None,
    scope_name: Optional[str] = None,
    upload_status: Optional[str] = None,
    name: Optional[str] = None,
    page: int = Query(1, ge=1),  # Default page is 1, and must be greater than or equal to 1
    limit: int = Query(1000, le=1000),  # Default limit is 10, maximum limit is 100
    db: Session = Depends(get_db)
):
    # Query the data
    query = db.query(Roads2025)
    
    #Apply filters if any
    if state_name:
        query = query.filter(Roads2025.state_name == state_name.replace(" ", "_").upper())
    if region:
        query = query.filter(Roads2025.region == region.replace(" ", "_").upper())
    if assigned_cam_number is not None:
        query = query.filter(Roads2025.assigned_cam_number == assigned_cam_number)
    if camera_number is not None:
        query = query.filter(Roads2025.camera_number == camera_number)
    if status is not None:
        query = query.filter(Roads2025.status == status)
    if collected_date:
        query = query.filter(Roads2025.collection_date == collected_date)
    if hub_id is not None:
        query = query.filter(Roads2025.hub_id == hub_id)
    if scope_name:
        query = query.filter(Roads2025.scope_name == scope_name)
    if upload_status:
        query = query.filter(Roads2025.upload_status == upload_status)
    if name:
        query = query.filter(Roads2025.name.ilike(f"%{name}%"))  # Case-insensitive partial match

    
    # Calculate offset for pagination
    offset = (page - 1) * limit

    # Sort by ID and paginate results
    query = query.order_by(Roads2025.id)
    
    total_count = query.count()

    # Query the data for the current page
    roads = query.offset(offset).limit(limit).all()

    # Calculate next and previous pages
    next_page = page + 1 if offset + limit < total_count else None
    previous_page = page - 1 if page > 1 else None

    return {
        "count": total_count,
        "next": next_page,
        "previous": previous_page,
        "results": roads,
    }
    
@router.get("/api/current-state/", response_model=CurrentStateResponse)
def get_current_state(db: Session = Depends(get_db)):
    # Query the database to find the active state
    active_state = db.query(models.Currentstate).filter(models.Currentstate.active == True).first()

    # If no active state is found, raise a 404 error
    if not active_state:
        raise HTTPException(status_code=404, detail="No active state found")

    # Return the active state
    return active_state



@router.get("/api/scope-hubs/", response_model=HubNamesResponse)
def get_scope_hubs(db: Session = Depends(get_db)):
    # Query the database to get all roads with their associated hubs
    roads_with_hubs = db.query(Roads2025.scope_name, Roads2025.state_name, Hubs2025.name).join(
        Hubs2025, Roads2025.hub_id == Hubs2025.id
    ).all()

    # If no data is found, raise a 404 error
    if not roads_with_hubs:
        raise HTTPException(status_code=404, detail="No data found")

    # Organize the data into the required structure
    result = {}
    for scope_name, state_name, hub_name in roads_with_hubs:
        # Convert state_name from Enum to string
        state_name_str = state_name.value  # Assuming StateNameEnum uses .value for the string representation

        if scope_name not in result:
            result[scope_name] = {}
        if state_name_str not in result[scope_name]:
            result[scope_name][state_name_str] = []
        if hub_name not in result[scope_name][state_name_str]:  # Avoid duplicates
            result[scope_name][state_name_str].append(hub_name)

    return {"scope_name": result}


@router.get("/api/get_camera_stat/{camera_number}")
def get_camera_stat(
    camera_number: int,
    state: Optional[str] = None,
    region: Optional[str] = None,
    hub_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Base query for total length of the specified camera_number
    camera_query = db.query(func.sum(Roads2025.length)).filter(
        Roads2025.camera_number == camera_number,
        Roads2025.status == 100
    )

    # Base query for total length of all roads (status == 100)
    total_query = db.query(func.sum(Roads2025.length)).filter(
        Roads2025.status == 100
    )

    # Apply optional filters to both queries
    if state:
        camera_query = camera_query.filter(Roads2025.state_name == state)
        total_query = total_query.filter(Roads2025.state_name == state)
    if region:
        camera_query = camera_query.filter(Roads2025.region == region)
        total_query = total_query.filter(Roads2025.region == region)
    if hub_id:
        camera_query = camera_query.filter(Roads2025.hub_id == hub_id)
        total_query = total_query.filter(Roads2025.hub_id == hub_id)
    if start_date and end_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        camera_query = camera_query.filter(
            Roads2025.collection_date >= start_date,
            Roads2025.collection_date <= end_date
        )
        total_query = total_query.filter(
            Roads2025.collection_date >= start_date,
            Roads2025.collection_date <= end_date
        )

    # Calculate total length for the specified camera_number
    camera_total_length = camera_query.scalar() or 0

    # Calculate total length for all roads (status == 100)
    all_total_length = total_query.scalar() or 0

    # Calculate percentage
    percentage = 0
    if all_total_length > 0:
        percentage = (camera_total_length / all_total_length) * 100

    # Calculate weekly report for the last 4 weeks
    weekly_report = []
    today = datetime.today().date()
    for week in range(4):
        week_start = today - timedelta(days=(today.weekday() + 7 * week))
        week_end = week_start + timedelta(days=6)

        # Query for the week's total length for the specified camera_number
        week_query = db.query(func.sum(Roads2025.length)).filter(
            Roads2025.camera_number == camera_number,
            Roads2025.status == 100,
            Roads2025.collection_date >= week_start,
            Roads2025.collection_date <= week_end
        )

        # Apply the same optional filters to the weekly query
        if state:
            week_query = week_query.filter(Roads2025.state_name == state)
        if region:
            week_query = week_query.filter(Roads2025.region == region)
        if hub_id:
            week_query = week_query.filter(Roads2025.hub_id == hub_id)

        week_total_length = week_query.scalar() or 0
        weekly_report.append(week_total_length)

    return {
        "camera_number": camera_number,
        "total_length": camera_total_length,
        "percentage": round(percentage, 2),  # Round to 2 decimal places
        "weekly_report": weekly_report
    }

@router.get("/api/get_2025_state_stats")
def get_2025_state_stats(
    hub_id: Optional[int] = None,
    region: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Base query to get total length covered (status == 100) and total length for each state
    query = db.query(
        Roads2025.state_name,
        func.sum(Roads2025.length).filter(Roads2025.status == 100).label("total_length_covered"),
        func.sum(Roads2025.length).label("total_length_all")
    ).group_by(Roads2025.state_name)

    # Apply optional filters
    if hub_id:
        query = query.filter(Roads2025.hub_id == hub_id)
    if region:
        query = query.filter(Roads2025.region == region)
    if start_date and end_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        query = query.filter(
            and_(
                Roads2025.collection_date >= start_date,
                Roads2025.collection_date <= end_date
            )
        )

    # Execute the query
    state_stats = query.all()

    # Calculate percentage_covered for each state
    result = []
    for state, total_length_covered, total_length_all in state_stats:
        # Handle None values
        total_length_covered = total_length_covered or 0
        total_length_all = total_length_all or 0

        # Calculate percentage_covered
        percentage_covered = 0
        if total_length_all > 0:
            percentage_covered = (total_length_covered / total_length_all) * 100

        result.append({
            "state": state,
            "total_length_covered": total_length_covered,
            "percentage_covered": round(percentage_covered, 2)  # Round to 2 decimal places
        })

    return result


@router.put("/api/update_2025_road")
def update_road(request: UpdateRoadRequest, db: Session = Depends(get_db)):
    # Find the row by road_name
    road = db.query(Roads2025).filter(Roads2025.name == request.road_name).first()
    if not road:
        raise HTTPException(status_code=404, detail="Road not found")

    # Update camera_number and vid_number
    road.camera_number = request.camera_number
    road.vid_number = request.vid_number

    # Update status to 100
    road.status = 100

    # Update collection_date or second_collection_date
    if request.collection_date:
        if road.collection_date:  # If collection_date is already filled
            road.second_collection_date = request.collection_date
        else:  # If collection_date is not filled
            road.collection_date = request.collection_date

    # Commit changes to the database
    db.commit()
    db.refresh(road)

    #Set current state
    db.query(models.Currentstate).update({"active": False})

    # Find or create the current state entry for the updated road's state
    current_state = db.query(models.Currentstate).filter(models.Currentstate.state == road.state_name).first()
    print(current_state.state)
    current_state.active = True
    db.commit()
    db.refresh(current_state)

    return {"message": "Road updated successfully", "road": road}


@router.get("/all-covered-2025-states/", response_model=StatesResponse)
def get_all_state_covered(db: Session = Depends(get_db)):
    # Step 1: Fetch all states where status == 100
    states_with_status_100 = (
        db.query(Roads2025.state_name)
        .filter(Roads2025.status == 100)
        .distinct()  # Ensure unique states
        .all()
    )

    # Extract state names from the query result
    state_names = [state.state_name for state in states_with_status_100]

    # Step 2: Fetch the active state from the Currentstate table
    active_state = db.query(models.Currentstate.state).filter(models.Currentstate.active == True).first()

    # Step 3: Arrange the states such that the active state is first
    if active_state and active_state.state in state_names:
        # Move the active state to the beginning of the list
        state_names.remove(active_state.state)  # Remove the active state from its current position
        state_names.insert(0, active_state.state)  # Insert it at the beginning

    # Step 4: Return the list of states
    return {"states": state_names}