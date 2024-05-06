from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional, Union, List
from passlib.context import CryptContext




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
    
    

