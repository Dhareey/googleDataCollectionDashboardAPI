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
    
class StateStatistics(BaseModel):
    Oyo: float
    Oyo_percent: float
    Oyo_start_date : str
    Ogun: float
    Ogun_percent: float
    Ogun_start_date : str
    Lagos: float
    Lagos_percent: float
    Lagos_start_date : str
    Osun: float
    Osun_percent: float
    Osun_start_date : str
    Ondo: float
    Ondo_percent: float
    Ondo_start_date : str
    Edo: float
    Edo_percent: float
    Edo_start_date : str
    Delta: float
    Delta_percent: float
    Delta_start_date : str
    
    
    
    
    
    
    
    

