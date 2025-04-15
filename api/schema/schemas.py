from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional, Union, List, Dict, Any
from passlib.context import CryptContext
from api.controllers.enum import StateNameEnum, RegionEnum, statusEnum




class CreateGoogleRoads(BaseModel):
    name: str
    length: float
    cam_name: Optional[str] = None
    camera_number: Optional[int] = None
    status: Optional[int] = None
    collection_date: Optional[date] = None
    upload_status: Optional[str] = None
    upload_date: Optional[date] = None
    state_name: Optional[str] = None
    state_code: Optional[str] = None
    region: Optional[str] = None
    geometry: List[List[float]]
    
    
class CreateCollectedRoads(BaseModel):
    name: str
    date: date
    camera_number: int
    geometry: List[List[float]]
    
class GetGoogleRoads(BaseModel):
    id: int
    name: str
    length: float
    status: int
    collection_date: date
    upload_status: str
    upload_date: date
    state_name: str
    state_code: str
    region: str
    geometry: List[List[float]]
    
    
class GetCollectedRoad(BaseModel):
    id: int
    name: str
    date: date
    camera_number: int
    geometry: List[List[float]]
    
class EditGoogleRoads(BaseModel):
    name: Optional[str] = None
    length: Optional[float] = None
    cam_name: Optional[str] = None
    camera_number: Optional[int] = None
    status: Optional[int] = None
    collection_date: Optional[date] = None
    upload_status: Optional[str] = None
    upload_date: Optional[date] = None
    state_name: Optional[str] = None
    state_code: Optional[str] = None
    region: Optional[str] = None
    
class GeneralStatistics(BaseModel):
    covered_km : float
    percent_covered : float
    total_uploads: int
    total_upload_km : float
    cam1_km : float
    cam1_percent: float
    cam2_km : float
    cam2_percent: float
    cam3_km : float
    cam3_percent: float
    cam4_km: float
    cam4_percent: float
    cam5_km: float
    cam5_percent: float
    cam6_km: float
    cam6_percent: float
    
class StateStatistics(BaseModel):
    Oyo: Union[float, str]
    Oyo_percent: Union[float, str]
    Oyo_start_date : Union[float, str]
    Ogun: Union[float, str]
    Ogun_percent: Union[float, str]
    Ogun_start_date : Union[float, str]
    Lagos: Union[float, str]
    Lagos_percent: Union[float, str]
    Lagos_start_date : Union[float, str]
    Osun: Union[float, str]
    Osun_percent: Union[float, str]
    Osun_start_date : Union[float, str]
    Ondo: Union[float, str]
    Ondo_percent: Union[float, str]
    Ondo_start_date : Union[float, str]
    Edo: Union[float, str]
    Edo_percent: Union[float, str]
    Edo_start_date : Union[float, str]
    Delta: Union[float, str]
    Delta_percent: Union[float, str]
    Delta_start_date : Union[float, str]
    
    
    
class CreateGoogleJsonRoads(BaseModel):
    name: str
    length: float
    cam_name: Optional[str] = None
    camera_number: Optional[int] = None
    status: Optional[int] = None
    collection_date: Optional[date] = None
    upload_status: Optional[str] = None
    upload_date: Optional[date] = None
    state_name: Optional[str] = None
    region: Optional[str] = None
    geometry: Optional[dict] = None
    
    
class EditGoogleJsonRoads(BaseModel):
    name: Optional[str] = None
    length: Optional[float] = None
    cam_name: Optional[str] = None
    camera_number: Optional[int] = None
    status: Optional[int] = None
    collection_date: Optional[date] = None
    upload_status: Optional[str] = None
    upload_date: Optional[date] = None
    state_name: Optional[str] = None
    region: Optional[str] = None
    geometry: Optional[dict] = None

    
class CameraCoverageSchema(BaseModel):
    id: int
    date: date
    camera_1_total: Optional[float] = None
    camera_2_total: Optional[float] = None
    camera_3_total: Optional[float] = None
    camera_4_total: Optional[float] = None
    camera_5_total: Optional[float] = None
    camera_6_total: Optional[float] = None
    
    
################################################################
##2025 SCHEMAS

class Hubs2025Response(BaseModel):
    id: int
    name: str
    total_road_length: float
    total_road_number: int
    geometry: List[List[List]]

    class Config:
        from_attributes=True
        
class PaginationResponse(BaseModel):
    count: int
    next: Optional[int] = None  # The page number of the next set of results
    previous: Optional[int] = None  # The page number of the previous set of results
    results: List[Hubs2025Response]
    
    
class Roads2025Response(BaseModel):
    id: int
    name: str
    length: float
    assigned_cam_number: Optional[int]
    camera_number: Optional[int]
    second_camera_number: Optional[str]
    status: statusEnum
    assignment_date: Optional[date]
    collection_date: Optional[date]
    second_collection_date: Optional[date]
    upload_status: str
    upload_date: Optional[date]
    state_name: StateNameEnum
    region: RegionEnum
    scope_name: str
    vid_number: Optional[str]
    container_id: Optional[str]
    ingestion_tracker: Optional[str]
    ingestion_tracker_date: Optional[date]
    collected_length: Optional[float]
    hub_id: int
    length_diff: float
    geometry: List[List]

    class Config:
        from_attributes=True
        
class PaginationRoadResponse(BaseModel):
    count: int
    next: Optional[int] = None  # The page number of the next set of results
    previous: Optional[int] = None  # The page number of the previous set of results
    results: List[Roads2025Response]
    
class CurrentStateResponse(BaseModel):
    id: int
    state: StateNameEnum
    coordinates: Dict[str, Any]
    active: bool

    class Config:
        from_attributes = True 
        
class HubInfo(BaseModel):
    id: int
    name: str

class HubNamesResponse(BaseModel):
    scope_name: Dict[str, Dict[str, List[HubInfo]]]

# Pydantic model for request body
class UpdateRoadRequest(BaseModel):
    road_name: str
    camera_number: int
    vid_number: str
    collection_date: Optional[date] = None
    
class StatesResponse(BaseModel):
    states: List[StateNameEnum]
    
class HubNamesFilter(BaseModel):
    hubnames: Optional[List[str]] = None

