from sqlalchemy import Column, String, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship
from database import Base
import uuid

class GeospatialFile(Base):
    __tablename__ = "geospatial_files"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, index=True)
    status = Column(String, default="PENDING")
    feature_count = Column(Integer, nullable=True)
    crs = Column(String, nullable=True)
    
    measurements = relationship("FeatureMeasurement", back_populates="file")

class FeatureMeasurement(Base):
    __tablename__ = "feature_measurements"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    file_id = Column(String, ForeignKey("geospatial_files.id"))
    feature_id = Column(String)
    geometry_type = Column(String)
    properties = Column(String)
    area_sqm = Column(Float, nullable=True)
    length_m = Column(Float, nullable=True)

    file = relationship("GeospatialFile", back_populates="measurements")

