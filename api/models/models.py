from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, Float, DateTime, JSON
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape

from core.database import Base

    
###################################################################################
    
    
class Googleroads(Base):
    __tablename__ = 'Google_Roads'
    
    id = Column(Integer, primary_key = True, index= True)
    name = Column(String, nullable = True)
    length = Column(Float, nullable = True)
    cam_name = Column(String, nullable = True)
    camera_number = Column(Integer, nullable = True)  # Camera
    status = Column(Integer, nullable = True)
    collection_date = Column(Date,  nullable = True)
    upload_status = Column(String, nullable = True)
    upload_date = Column(Date, nullable= True)
    state_name = Column(String, nullable= True)
    state_code = Column(String, nullable = True)
    region = Column(String, nullable= True)
    geometry = Column(Geometry(geometry_type="LINESTRING", srid=4326))
    
    

    
class Google_Roads_Json(Base):
    __tablename__ = 'google_roads_json'
    
    id = Column(Integer, primary_key = True, index= True)
    name = Column(String, nullable = True)
    length = Column(Float, nullable = True)
    cam_name = Column(String, nullable = True)
    camera_number = Column(Integer, nullable = True)  # Camera
    status = Column(Integer, nullable = True)
    collection_date = Column(Date,  nullable = True)
    upload_status = Column(String, nullable = True)
    upload_date = Column(Date, nullable= True)
    state_name = Column(String, nullable= True)
    region = Column(String, nullable= True)
    scope_name = Column(String, nullable= True)
    geometry = Column(JSON, nullable = True)
    
    # Foreign key to Hubs
    hub_id = Column(Integer, ForeignKey('Hubs_data.id'), nullable=True)

    # Relationship to Hubs
    hub = relationship("Hubs", back_populates="roads")
    
class CameraCoverage(Base):
    __tablename__ = "camera_coverage"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable= False)
    camera_1_total = Column(Float, nullable=True)
    camera_2_total = Column(Float, nullable=True)
    camera_3_total = Column(Float, nullable=True)
    camera_4_total = Column(Float, nullable=True)
    camera_5_total = Column(Float, nullable=True)
    camera_6_total = Column(Float, nullable= True)
    
####################################################################################################
## Hubs database

class Hubs(Base):
    __tablename__ = "Hubs_data"
    
    id = Column(Integer, primary_key =True, index=True)
    name = Column(String, nullable=True)
    total_road_length = Column(Float, nullable= True)
    total_road_number = Column(Integer, nullable = True)
    state = Column(String, nullable= True)
    region = Column(String, nullable= True)
    geometry = Column(JSON, nullable = True)
    
    # Relationship to Google Roads
    roads = relationship("Google_Roads_Json", back_populates = "hub")
    