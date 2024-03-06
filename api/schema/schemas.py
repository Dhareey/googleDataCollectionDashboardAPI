from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional, Union, List
from passlib.context import CryptContext




class CreateGoogleRoads(BaseModel):
    name: str
    length: float
    camera_number: Optional[int]
    status: int
    collection_date: Optional[date]
    upload_status: Optional[str]
    upload_date: Optional[date]
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
    geometry: List[List[float]]
    
    
class GetCollectedRoad(BaseModel):
    id: int
    name: str
    date: date
    camera_number: int
    geometry: List[List[float]]
    
    
    

