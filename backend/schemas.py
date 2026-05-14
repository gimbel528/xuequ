from pydantic import BaseModel
from typing import Optional, List

class SchoolBase(BaseModel):
    name: str
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = "#3388ff"

class SchoolCreate(SchoolBase):
    pass

class SchoolUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None

class SchoolResponse(SchoolBase):
    id: int
    longitude: Optional[float] = None
    latitude: Optional[float] = None

    class Config:
        from_attributes = True

class DistrictBase(BaseModel):
    school_id: int
    coordinates: str

class DistrictCreate(DistrictBase):
    pass

class DistrictUpdate(BaseModel):
    coordinates: str

class DistrictResponse(DistrictBase):
    id: int

    class Config:
        from_attributes = True

class CommunityBase(BaseModel):
    name: str
    coordinates: str

class CommunityCreate(CommunityBase):
    pass

class CommunityUpdate(BaseModel):
    name: Optional[str] = None
    coordinates: Optional[str] = None

class CommunityResponse(CommunityBase):
    id: int
    school_id: int

    class Config:
        from_attributes = True

class SchoolWithDistrict(SchoolResponse):
    has_district: bool = False
    coordinates: Optional[str] = None
    communities: List[CommunityResponse] = []

    class Config:
        from_attributes = True
