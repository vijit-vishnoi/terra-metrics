from pydantic import BaseModel, ConfigDict
from typing import Optional

class FileResponse(BaseModel):
    id: str
    filename: str
    status: str
    feature_count: Optional[int] = None
    crs: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class FeatureMeasurementResponse(BaseModel):
    feature_id: str
    geometry_type: str
    properties: str
    area_sqm: Optional[float] = None
    length_m: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)

class MeasurementResponse(BaseModel):
    id: str
    measurements: list[FeatureMeasurementResponse] = []
