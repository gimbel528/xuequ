from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pydantic import BaseModel
from typing import Optional, List
import os
import httpx

# 数据库配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'schools.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 数据模型
class School(Base):
    __tablename__ = "schools"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address = Column(String(200))
    phone = Column(String(50))
    description = Column(Text)
    color = Column(String(20), default="#3388ff")
    longitude = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    district = relationship("District", back_populates="school", uselist=False)
    communities = relationship("Community", back_populates="school", cascade="all, delete-orphan")

class District(Base):
    __tablename__ = "districts"
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), unique=True)
    coordinates = Column(Text, nullable=False)
    school = relationship("School", back_populates="district")

class Community(Base):
    __tablename__ = "communities"
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    name = Column(String(100), nullable=False)
    coordinates = Column(Text, nullable=False)
    school = relationship("School", back_populates="communities")

# 初始化数据库
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Schemas
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
    class Config: from_attributes = True

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
    class Config: from_attributes = True

class SchoolWithDistrict(SchoolResponse):
    has_district: bool = False
    coordinates: Optional[str] = None
    communities: List[CommunityResponse] = []
    class Config: from_attributes = True

# FastAPI App
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AMAP_WEB_KEY = "fa00396c785cea9ca43456e42fd099e6"

async def geocode_school(name: str, address: str = None):
    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {"key": AMAP_WEB_KEY, "address": f"大连金普新区{name}", "city": "大连"}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=5)
            data = response.json()
            if data.get("status") == "1" and data.get("geocodes"):
                location = data["geocodes"][0].get("location")
                if location:
                    lng, lat = location.split(",")
                    return float(lng), float(lat)
    except Exception as e:
        print(f"Geocode error: {e}")
    return None

# Routes
@app.get("/")
def root():
    return {"message": "School District API", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/schools", response_model=List[SchoolWithDistrict])
def get_schools(db: Session = Depends(get_db)):
    schools = db.query(School).all()
    result = []
    for school in schools:
        communities = db.query(Community).filter(Community.school_id == school.id).all()
        communities_data = [
            CommunityResponse(id=c.id, school_id=c.school_id, name=c.name, coordinates=c.coordinates) 
            for c in communities
        ]
        school_data = SchoolWithDistrict(
            id=school.id, name=school.name, address=school.address, phone=school.phone,
            description=school.description, color=school.color,
            longitude=school.longitude, latitude=school.latitude,
            has_district=school.district is not None or len(communities) > 0,
            coordinates=school.district.coordinates if school.district else None,
            communities=communities_data
        )
        result.append(school_data)
    return result

@app.get("/api/schools/{school_id}", response_model=SchoolWithDistrict)
def get_school(school_id: int, db: Session = Depends(get_db)):
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise Exception("学校不存在")
    communities = db.query(Community).filter(Community.school_id == school.id).all()
    communities_data = [
        CommunityResponse(id=c.id, school_id=c.school_id, name=c.name, coordinates=c.coordinates) 
        for c in communities
    ]
    return SchoolWithDistrict(
        id=school.id, name=school.name, address=school.address, phone=school.phone,
        description=school.description, color=school.color,
        longitude=school.longitude, latitude=school.latitude,
        has_district=school.district is not None or len(communities) > 0,
        coordinates=school.district.coordinates if school.district else None,
        communities=communities_data
    )

@app.post("/api/schools", response_model=SchoolResponse)
async def create_school(school: SchoolCreate, db: Session = Depends(get_db)):
    db_school = School(**school.model_dump())
    coords = await geocode_school(school.name, school.address)
    if coords:
        db_school.longitude, db_school.latitude = coords
    db.add(db_school)
    db.commit()
    db.refresh(db_school)
    return db_school

@app.put("/api/schools/{school_id}", response_model=SchoolResponse)
async def update_school(school_id: int, school: SchoolUpdate, db: Session = Depends(get_db)):
    db_school = db.query(School).filter(School.id == school_id).first()
    if not db_school:
        raise Exception("学校不存在")
    update_data = school.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_school, key, value)
    if (school.name or school.address) and school.longitude is None and school.latitude is None:
        name = school.name or db_school.name
        address = school.address if school.address else db_school.address
        coords = await geocode_school(name, address)
        if coords:
            db_school.longitude, db_school.latitude = coords
    db.commit()
    db.refresh(db_school)
    return db_school

@app.delete("/api/schools/{school_id}")
def delete_school(school_id: int, db: Session = Depends(get_db)):
    db_school = db.query(School).filter(School.id == school_id).first()
    if not db_school:
        raise Exception("学校不存在")
    db.delete(db_school)
    db.commit()
    return {"message": "删除成功"}

# Communities Routes
@app.get("/api/communities/school/{school_id}", response_model=List[CommunityResponse])
def get_communities_by_school(school_id: int, db: Session = Depends(get_db)):
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise Exception("学校不存在")
    return db.query(Community).filter(Community.school_id == school_id).all()

@app.post("/api/communities", response_model=CommunityResponse)
def create_community(community: CommunityCreate, school_id: int, db: Session = Depends(get_db)):
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise Exception("学校不存在")
    db_community = Community(school_id=school_id, name=community.name, coordinates=community.coordinates)
    db.add(db_community)
    db.commit()
    db.refresh(db_community)
    return db_community

@app.put("/api/communities/{community_id}", response_model=CommunityResponse)
def update_community(community_id: int, community: CommunityUpdate, db: Session = Depends(get_db)):
    db_community = db.query(Community).filter(Community.id == community_id).first()
    if not db_community:
        raise Exception("小区不存在")
    update_data = community.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_community, key, value)
    db.commit()
    db.refresh(db_community)
    return db_community

@app.delete("/api/communities/{community_id}")
def delete_community(community_id: int, db: Session = Depends(get_db)):
    db_community = db.query(Community).filter(Community.id == community_id).first()
    if not db_community:
        raise Exception("小区不存在")
    db.delete(db_community)
    db.commit()
    return {"message": "删除成功"}
