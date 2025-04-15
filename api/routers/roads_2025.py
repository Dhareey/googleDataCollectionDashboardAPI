from fastapi import APIRouter, status, Depends, HTTPException, BackgroundTasks, Query, Body, UploadFile, File
#from api.schema.schemas import HubSchema, UserSchema
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import get_db
from api.models.models import Hubs2025, Roads2025
from core.database import get_async_session
from fastapi.responses import JSONResponse
###############################################################
from api.schema.schemas import (
    Hubs2025Response,
    PaginationResponse,
    PaginationRoadResponse,
    CurrentStateResponse,
    Hubs2025Response,
    PaginationResponse,
    PaginationRoadResponse,
    HubNamesResponse,
    UpdateRoadRequest,
    StatesResponse,
    HubNamesFilter
)
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.future import select
#from api.models.models import Road
from api.repository.roads_repo_2025 import parse_uploaded_file
from datetime import datetime, date
from sqlalchemy import func, case, and_, or_

from shapely.geometry import MultiLineString, LineString, shape
from geoalchemy2 import WKBElement
from shapely import wkb
from typing import List
from api.models.models import Google_Roads_Json
from api.models import models
from api.tasks.tasks import update_camera_coverage_background
from api.routers.roads import paginate
from api.controllers.enum import statusEnum, StateNameEnum, RegionEnum
import logging

router_2025 = APIRouter(tags=['Roads_2025'])

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

####################################################################################################
###2025 ENDPOINTS

# GET all 2025 Hubs with pagination
@router_2025.get("/hubs_2025", response_model=list[Hubs2025Response])
async def get_all_hubs(
    page: int = Query(1, ge=1),  # Default page = 1
    session: AsyncSession = Depends(get_async_session),
):
    query = select(Hubs2025)
    paginated_query = paginate(query, page, 1000)  # 1000 rows per page
    result = await session.execute(paginated_query)
    return result.scalars().all()

@router_2025.get("/api/hubs", status_code=status.HTTP_200_OK, response_model=PaginationResponse)
async def get_all_2005_hubs(
    page: int = Query(1, ge=1),  # Default page is 1, and must be greater than or equal to 1
    limit: int = Query(1000, le=1000),  # Default limit is 10, maximum limit is 100
    hub_names: Optional[List[str]] = Query(None),  # Optional list of hub names to filter by
    db: Session = Depends(get_db)
):
    # Calculate offset for pagination
    offset = (page - 1) * limit

    # Query the database with offset and limit
    query = db.query(Hubs2025)
    
    # Apply hub name filter if hub_names is provided
    if hub_names:
        # Use SQLAlchemy's `or_` to filter by any of the provided hub names
        query = query.filter(or_(Hubs2025.name.in_(hub_names)))

    # Get the total count of hubs (after applying filters)
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
    
@router_2025.get("/api/roads_2025", status_code=status.HTTP_200_OK, response_model=PaginationRoadResponse)
async def get_all_2025_roads(
    state_names: Optional[List[str]] = Query(None),
    regions: Optional[List[str]] = Query(None),
    assigned_cam_number: Optional[int] = None,
    camera_number: Optional[int] = None,
    status: Optional[int] = None,
    collected_date: Optional[str] = None,
    hub_ids: Optional[List[int]] = Query(None),
    scope_name: Optional[str] = None,
    upload_status: Optional[str] = None,
    name: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(1000, le=1000),
    db: Session = Depends(get_db)
):
    # Query the data
    query = db.query(Roads2025)
    
    # Convert and apply state filters
    if state_names:
        try:
            state_enums = [StateNameEnum.from_string(state) for state in state_names]
            query = query.filter(Roads2025.state_name.in_(state_enums))
        except ValueError as e:
            valid_states = [e.value for e in StateNameEnum]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid state name: {str(e)}. Valid states are: {valid_states}"
            )

    # Convert and apply region filters
    if regions:
        try:
            region_enums = [RegionEnum.from_string(region) for region in regions]
            query = query.filter(Roads2025.region.in_(region_enums))
        except ValueError as e:
            valid_regions = [e.value for e in RegionEnum]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid region name: {str(e)}. Valid regions are: {valid_regions}"
            )

    # Apply other filters
    if assigned_cam_number is not None:
        query = query.filter(Roads2025.assigned_cam_number == assigned_cam_number)
    if camera_number is not None:
        query = query.filter(Roads2025.camera_number == camera_number)
    if status is not None:
        query = query.filter(Roads2025.status == status)
    if collected_date:
        query = query.filter(Roads2025.collection_date == collected_date)
    if hub_ids:
        query = query.filter(Roads2025.hub_id.in_(hub_ids))
    if scope_name:
        query = query.filter(Roads2025.scope_name == scope_name)
    if upload_status:
        query = query.filter(Roads2025.upload_status == upload_status)
    if name:
        query = query.filter(Roads2025.name.ilike(f"%{name}%"))

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
    
@router_2025.get("/api/current-state/", response_model=CurrentStateResponse)
def get_current_state(db: Session = Depends(get_db)):
    # Query the database to find the active state
    active_state = db.query(models.Currentstate).filter(models.Currentstate.active == True).first()

    # If no active state is found, raise a 404 error
    if not active_state:
        raise HTTPException(status_code=404, detail="No active state found")

    # Return the active state
    return active_state



@router_2025.get("/api/scope-hubs/", response_model=HubNamesResponse)
def get_scope_hubs(db: Session = Depends(get_db)):
    # Query the database to get all roads with their associated hubs (now including hub id)
    roads_with_hubs = db.query(
        Roads2025.scope_name, 
        Roads2025.state_name, 
        Hubs2025.name,
        Hubs2025.id  # Add hub id to the query
    ).join(
        Hubs2025, Roads2025.hub_id == Hubs2025.id
    ).all()

    # If no data is found, raise a 404 error
    if not roads_with_hubs:
        raise HTTPException(status_code=404, detail="No data found")

    # Organize the data into the required structure
    result = {}
    for scope_name, state_name, hub_name, hub_id in roads_with_hubs:
        # Convert state_name from Enum to string
        state_name_str = state_name.value

        if scope_name not in result:
            result[scope_name] = {}
        if state_name_str not in result[scope_name]:
            result[scope_name][state_name_str] = []
        
        # Check if hub already exists in the list (avoid duplicates)
        hub_exists = False
        for hub in result[scope_name][state_name_str]:
            if hub['id'] == hub_id:  # Check by ID to avoid duplicates
                hub_exists = True
                break
                
        if not hub_exists:
            result[scope_name][state_name_str].append({
                "id": hub_id,
                "name": hub_name
            })

    return {"scope_name": result}


@router_2025.get("/api/get_camera_stat/{camera_number}")
def get_camera_stat(
    camera_number: int,
    states: Optional[List[str]] = Query(None),
    regions: Optional[List[str]] = Query(None),
    hub_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Convert string states to enum values if states are provided
    state_enums = []
    if states:
        try:
            state_enums = [StateNameEnum.from_string(state) for state in states]
        except ValueError as e:
            valid_states = [e.value for e in StateNameEnum]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid state name: {str(e)}. Valid states are: {valid_states}"
            )

    # Convert string regions to enum values if regions are provided
    region_enums = []
    if regions:
        try:
            region_enums = [RegionEnum.from_string(region) for region in regions]
        except ValueError as e:
            valid_regions = [e.value for e in RegionEnum]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid region name: {str(e)}. Valid regions are: {valid_regions}"
            )

    # Base query for total length of the specified camera_number
    camera_query = db.query(func.sum(Roads2025.length)).filter(
        Roads2025.camera_number == camera_number,
        Roads2025.status == statusEnum.COMPLETED
    )

    # Base query for total length of all roads (status == 100)
    total_query = db.query(func.sum(Roads2025.length)).filter(
        Roads2025.status == statusEnum.COMPLETED
    )

    # Apply optional filters to both queries
    if state_enums:
        camera_query = camera_query.filter(Roads2025.state_name.in_(state_enums))
        total_query = total_query.filter(Roads2025.state_name.in_(state_enums))
    if region_enums:
        camera_query = camera_query.filter(Roads2025.region.in_(region_enums))
        total_query = total_query.filter(Roads2025.region.in_(region_enums))
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
            Roads2025.status == statusEnum.COMPLETED,
            Roads2025.collection_date >= week_start,
            Roads2025.collection_date <= week_end
        )

        # Apply the same optional filters to the weekly query
        if state_enums:
            week_query = week_query.filter(Roads2025.state_name.in_(state_enums))
        if region_enums:
            week_query = week_query.filter(Roads2025.region.in_(region_enums))
        if hub_id:
            week_query = week_query.filter(Roads2025.hub_id == hub_id)

        week_total_length = week_query.scalar() or 0
        weekly_report.append(round(week_total_length, 1))

    return {
        "camera_number": camera_number,
        "total_length": round(camera_total_length, 2),
        "percentage": round(percentage, 2),
        "weekly_report": weekly_report
    }

@router_2025.get("/api/get_2025_state_stats")
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
        func.sum(Roads2025.length).filter(Roads2025.status == statusEnum.COMPLETED).label("total_length_covered"),
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


@router_2025.put("/api/update_2025_road")
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


@router_2025.get("/api/all-covered-2025-states/")
def get_all_state_covered(db: Session = Depends(get_db)):
    # Step 1: Fetch all roads with status == COMPLETED
    completed_roads = (
        db.query(Roads2025.state_name, Roads2025.vid_number)
        .filter(Roads2025.status == statusEnum.COMPLETED)
        .filter(Roads2025.vid_number.isnot(None))  # Ensure vid_number is not NULL
        .all()
    )

    # Step 2: Group vid_numbers by state_name using a set to avoid duplicates
    state_to_vid_numbers = {}
    for state_name, vid_number in completed_roads:
        if state_name not in state_to_vid_numbers:
            state_to_vid_numbers[state_name] = set()
        state_to_vid_numbers[state_name].add(vid_number)

    # Step 3: Fetch the active state from the Currentstate table
    active_state = db.query(models.Currentstate.state).filter(models.Currentstate.active == True).first()

    # Step 4: Reorder the dictionary to place the active state first (if it exists)
    if active_state and active_state.state in state_to_vid_numbers:
        active_state_data = {active_state.state: state_to_vid_numbers.pop(active_state.state)}
        state_to_vid_numbers = {**active_state_data, **state_to_vid_numbers}

    # Step 5: Return the dictionary
    return state_to_vid_numbers

@router_2025.get("/api/get_all_cameras_stat/")
def get_all_cameras_stat(
    states: Optional[List[str]] = Query(None),
    regions: Optional[List[str]] = Query(None),
    hub_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Convert string states to enum values if states are provided
    state_enums = []
    if states:
        try:
            state_enums = [StateNameEnum.from_string(state) for state in states]
        except ValueError as e:
            valid_states = [e.value for e in StateNameEnum]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid state name: {str(e)}. Valid states are: {valid_states}"
            )

    # Convert string regions to enum values if regions are provided
    region_enums = []
    if regions:
        try:
            region_enums = [RegionEnum.from_string(region) for region in regions]
        except ValueError as e:
            valid_regions = [e.value for e in RegionEnum]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid region name: {str(e)}. Valid regions are: {valid_regions}"
            )

    # Base query for total length of all roads (status == 100) for all cameras
    total_query = db.query(func.sum(Roads2025.length)).filter(
        Roads2025.status == statusEnum.COMPLETED
    )

    # Apply optional filters to the total query
    if state_enums:
        total_query = total_query.filter(Roads2025.state_name.in_(state_enums))
    if region_enums:
        total_query = total_query.filter(Roads2025.region.in_(region_enums))
    if hub_id:
        total_query = total_query.filter(Roads2025.hub_id == hub_id)
    if start_date and end_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        total_query = total_query.filter(
            Roads2025.collection_date >= start_date,
            Roads2025.collection_date <= end_date
        )

    # Calculate total length for all roads (status == 100)
    all_total_length = total_query.scalar() or 0

    # Calculate percentage coverage (assuming total_length is the same as all_total_length)
    percentage = 100  # Since we're considering all cameras, coverage is 100%

    # Calculate weekly report for the last 10 weeks
    weekly_report = []
    today = datetime.today().date()
    for week in range(10):
        week_start = today - timedelta(days=(today.weekday() + 7 * week))
        week_end = week_start + timedelta(days=6)

        # Query for the week's total length for all cameras
        week_query = db.query(func.sum(Roads2025.length)).filter(
            Roads2025.status == statusEnum.COMPLETED,
            Roads2025.collection_date >= week_start,
            Roads2025.collection_date <= week_end
        )

        # Apply the same optional filters to the weekly query
        if state_enums:
            week_query = week_query.filter(Roads2025.state_name.in_(state_enums))
        if region_enums:
            week_query = week_query.filter(Roads2025.region.in_(region_enums))
        if hub_id:
            week_query = week_query.filter(Roads2025.hub_id == hub_id)

        week_total_length = week_query.scalar() or 0
        weekly_report.append(round(week_total_length, 2))

    return {
        "total_length": round(all_total_length, 2),
        "percentage": round(percentage, 1),
        "weekly_report": weekly_report
    }
    
@router_2025.post("/api/update_2025_data")
async def update_roads_froom_csv(file: UploadFile = File(..., description="CSV file with road data updates"),db: Session = Depends(get_db)):
    
    """
    Update roads data from uploaded CSV file.
    
    The CSV must contain these mandatory columns:
    - road_name (new): Road identifier
    - camera_num: Camera number
    - status_1: Collection status
    - length_12: Collected length
    - collection: Collection date
    - upload_sta: Upload status
    - VID: VID number
    - Container ID: Container identifier
    """
    logger.info(f"Starting road data update from file: {file.filename}")
    data_rows = await parse_uploaded_file(file, "roads")
    
    if not data_rows:
        return JSONResponse(
                status_code=400,
                content={"message": "No data rows found in the file"}
            )
        
    logger.info(f"Found {len(data_rows)} valid rows to process")
    
    # Step 2: Process updates
    update_counts = {
            "total_rows": len(data_rows),
            "successful_updates": 0,
            "failed_updates": 0,
            "skipped_rows": 0
        }
    
    for row in data_rows:
        try:
            road = db.query(Roads2025).filter(
                Roads2025.name == row['road_name (new)']
            ).first()
                
            if not road:
                update_counts['skipped_rows'] += 1
                logger.warning(f"Road not found: {row['road_name (new)']}")
                continue
                
            # Update fields (with validation)
            if row['cam_no']:
                road.camera_number = int(row['cam_no'].replace("camera", ""))
                
            if row['status']:
                current_length = road.length
                road_status = row['status'].strip()
                if road_status == "completed":
                    road.status = statusEnum.COMPLETED
                    road.collected_length = current_length
                else:
                    current_collected_length = road.collected_length
                    proposed_length = road.collected_length + float(row["lenn (Timi)"])
                    if proposed_length >= current_length:
                        road.status = statusEnum.COMPLETED
                        road.collected_length = current_length
                    else:
                        road.status = statusEnum.IN_PROGRESS
                        road.collected_length = proposed_length
                
            if row['File Name']:
                filename = row['File Name'].strip()
                collection_date = filename.split("_")[1]
                try:
                    road.collection_date = datetime.strptime(
                            collection_date, 
                            '%Y%m%d'
                    ).date()
                except ValueError:
                        logger.warning(f"Invalid date format for {collection_date}")
                ##Update vid number
                road.vid_number = filename
                
            if row['Upload_status']:
                road.upload_status = row['Upload_status'].strip()
                
            if row["Container ID"]:
                road.container_id = row["Container ID"].strip()
                
            if row["Usability"]:
                road.ingestion_tracker = row["Usability"].strip()
                
            db.commit()
            update_counts['successful_updates'] += 1
            
        except Exception as e:
            db.rollback()
            update_counts['failed_updates'] += 1
            logger.error(f"Error updating {row.get('road_name (new)', 'unknown')}: {str(e)}")

    return {
        "message": "Road data update processed",
            "results": update_counts,
            "details": {
                "successful": update_counts['successful_updates'],
                "failed": update_counts['failed_updates'],
                "skipped": update_counts['skipped_rows']
            }
        }
    


@router_2025.post("/api/update_hubs_from_csv/")
async def update_hubs_from_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Read and validate CSV
    logger.info(f"Starting road data update from file: {file.filename}")
    data_rows = await parse_uploaded_file(file, "hubs")
    
    if not data_rows:
        return JSONResponse(
                status_code=400,
                content={"message": "No data rows found in the file"}
            )
        
    logger.info(f"Found {len(data_rows)} valid rows to process")
    
     # Step 2: Process updates
    update_counts = {
            "updated_hubs": [],
            "skipped_hubs": [],
            "errors": [],
            "skipped_rows": 0
        }
        
    for row in data_rows:
        try:
            # Skip if target_distance_available is 0 or empty
            if not row['target_distance_available'] or float(row['target_distance_available']) == 0:
                update_counts['skipped_hubs'].append(row['driving_hub_name'])
                continue
                
            # Normalize hub name (lowercase + remove spaces)
            normalized_name = row['driving_hub_name'].lower().replace(" ", "")
                
            # Find matching hub
            hub = db.query(Hubs2025).filter(
                    func.lower(func.replace(Hubs2025.name, " ", "")).ilike(f"%{normalized_name}%")
                ).first()
                
            if not hub:
                update_counts['errors'].append(f"Hub not found for '{row['driving_hub_name']}'")
                continue
                
            # Update hub fields
            hub.google_total_covered_km = float(row['target_distance_collected'])
            hub.google_total_available_length = float(row['target_distance_available'])
            hub.last_updated = datetime.now().date()
                
            update_counts['updated_hubs'].append(hub.name)
                
        except ValueError as e:
            update_counts['errors'].append(f"Row {row['target_distance_available']}: Invalid number format - {str(e)}")
        except Exception as e:
            update_counts['errors'].append(f"Row {row['target_distance_available']}: Error processing - {str(e)}")
        
    # Commit all changes if no errors
    db.commit()
    return {
                "message": "Update successful",
                "updated_hubs": update_counts['updated_hubs'],
                "skipped_hubs":update_counts['skipped_hubs'],
                "error_count": len(update_counts['errors'])
            }
    
@router_2025.get("/api/reconciliation/", response_model=List[dict])
def get_hub_road_statistics(
    states: Optional[List[str]] = Query(None),
    regions: Optional[List[str]] = Query(None),
    hub_ids: Optional[List[int]] = Query(None),
    db: Session = Depends(get_db)
):
    try:
        # Convert string states/regions to enums
        state_enums = []
        if states:
            try:
                state_enums = [StateNameEnum.from_string(state) for state in states]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        region_enums = []
        if regions:
            try:
                region_enums = [RegionEnum.from_string(region) for region in regions]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

        # Base query for hubs
        hub_query = db.query(Hubs2025)

        # Apply filters
        if state_enums:
            hub_query = hub_query.join(Roads2025).filter(
                Roads2025.state_name.in_(state_enums)
            )
        if region_enums:
            hub_query = hub_query.join(Roads2025).filter(
                Roads2025.region.in_(region_enums)
            )
        if hub_ids:
            hub_query = hub_query.filter(Hubs2025.id.in_(hub_ids))

        # Get all matching hubs
        hubs = hub_query.all()
        
        result = []
        
        for hub in hubs:
            # Get all roads for this hub
            roads_query = db.query(Roads2025).filter(
                Roads2025.hub_id == hub.id
            )
            
            # Apply state/region filters to roads too
            if state_enums:
                roads_query = roads_query.filter(
                    Roads2025.state_name.in_(state_enums)
                )
            if region_enums:
                roads_query = roads_query.filter(
                    Roads2025.region.in_(region_enums)
                )
            
            all_roads = roads_query.all()
            
            # Calculate statistics
            stats = {
                "total_length_covered": sum(r.collected_length for r in all_roads),
                "total_number_of_completed_road": sum(
                    1 for r in all_roads if r.status == statusEnum.COMPLETED
                ),
                "total_number_of_half_completed": sum(
                    1 for r in all_roads if r.status == statusEnum.IN_PROGRESS
                ),
                "total_available_km_OEA": hub.total_road_length,
                "total_available_km_Google": hub.google_total_available_length,
                "total_number_of_roads": hub.total_road_number,
                "total_km_uploaded_roads": sum(
                    r.collected_length for r in all_roads 
                    if r.upload_status in ["DONE", "FAILED"]
                ),
                "total_km_success_uploads": sum(
                    r.collected_length for r in all_roads 
                    if r.upload_status == "DONE"
                ),
                "total_km_failed_uploads": sum(
                    r.collected_length for r in all_roads 
                    if r.upload_status == "FAILED"
                ),
                "total_number_success_uploads": sum(
                    1 for r in all_roads if r.upload_status == "DONE"
                ),
                "total_number_failed_uploads": sum(
                    1 for r in all_roads if r.upload_status == "FAILED"
                ),
                "total_number_success_ingestion": sum(
                    1 for r in all_roads if r.ingestion_tracker == "PROCESSED"
                ),
                "total_km_success_ingestion": sum(
                    r.collected_length for r in all_roads 
                    if r.ingestion_tracker == "PROCESSED"
                ),
                "roads_data": [
                    {
                        "name": r.name,
                        "length": r.length,
                        "camera_number": r.camera_number,
                        "status": r.status.value,
                        "collection_date": r.collection_date.isoformat() if r.collection_date else None,
                        "upload_status": r.upload_status,
                        "vid_number": r.vid_number,
                        "container_id": r.container_id,
                        "ingestion_tracker": r.ingestion_tracker,
                        "collected_length": r.collected_length
                    } for r in all_roads
                ]
            }
            
            result.append({
                hub.name: stats
            })
            
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing request: {str(e)}"
        )