from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, Float, DateTime
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
    camera_number = Column(Integer, nullable = True)  # Camera
    status = Column(Integer, nullable = True)
    collection_date = Column(Date,  nullable = True)
    upload_status = Column(String, nullable = True)
    upload_date = Column(Date, nullable= True)
    geometry = Column(Geometry(geometry_type="LINESTRING", srid=4326))
    
    
class collectedRoads(Base):
    __tablename__ = "collected_roads"
    
    id = Column(Integer, primary_key=True, index= True)
    name = Column(String, nullable = True)
    date = Column(Date, nullable = True)
    camera_number = Column(Integer, nullable = True)
    geometry = Column(Geometry(geometry_type="LINESTRING", srid=4326))
    


    
    



    
    
    
    

    
    
    

    