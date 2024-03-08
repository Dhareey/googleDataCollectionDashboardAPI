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
    
    
    

