import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import School, Community
from schemas import SchoolCreate, SchoolUpdate, SchoolResponse, SchoolWithDistrict, CommunityResponse

router = APIRouter(prefix="/schools", tags=["schools"])

AMAP_WEB_KEY = "fa00396c785cea9ca43456e42fd099e6"

async def geocode_school(name: str, address: str = None) -> tuple[float, float] | None:
    url = "https://restapi.amap.com/v5/place/text"
    
    keywords = f"大连金普新区{name}"
    if address:
        keywords = f"大连金普新区{address}"
    
    params = {
        "key": AMAP_WEB_KEY,
        "keywords": keywords,
        "city": "大连",
        "types": "141201",
        "page_size": 5
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=5)
            data = response.json()
            
            if data.get("status") == "1" and data.get("pois"):
                for poi in data["pois"]:
                    if name in poi.get("name", ""):
                        location = poi.get("location")
                        if location:
                            lng, lat = location.split(",")
                            return float(lng), float(lat)
                
                poi = data["pois"][0]
                location = poi.get("location")
                if location:
                    lng, lat = location.split(",")
                    return float(lng), float(lat)
    except Exception as e:
        print(f"POI搜索失败: {e}")
    
    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {
        "key": AMAP_WEB_KEY,
        "address": f"大连金普新区{name}",
        "city": "大连"
    }
    
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
        print(f"地理编码失败: {e}")
    
    return None

@router.get("/", response_model=List[SchoolWithDistrict])
def get_schools(db: Session = Depends(get_db)):
    schools = db.query(School).all()
    result = []
    for school in schools:
        communities = db.query(Community).filter(Community.school_id == school.id).all()
        communities_data = [
            CommunityResponse(
                id=c.id,
                school_id=c.school_id,
                name=c.name,
                coordinates=c.coordinates
            ) for c in communities
        ]
        
        school_data = SchoolWithDistrict(
            id=school.id,
            name=school.name,
            address=school.address,
            phone=school.phone,
            description=school.description,
            color=school.color,
            longitude=school.longitude,
            latitude=school.latitude,
            has_district=school.district is not None or len(communities) > 0,
            coordinates=school.district.coordinates if school.district else None,
            communities=communities_data
        )
        result.append(school_data)
    return result

@router.get("/{school_id}", response_model=SchoolWithDistrict)
def get_school(school_id: int, db: Session = Depends(get_db)):
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")
    
    communities = db.query(Community).filter(Community.school_id == school.id).all()
    communities_data = [
        CommunityResponse(
            id=c.id,
            school_id=c.school_id,
            name=c.name,
            coordinates=c.coordinates
        ) for c in communities
    ]
    
    return SchoolWithDistrict(
        id=school.id,
        name=school.name,
        address=school.address,
        phone=school.phone,
        description=school.description,
        color=school.color,
        longitude=school.longitude,
        latitude=school.latitude,
        has_district=school.district is not None or len(communities) > 0,
        coordinates=school.district.coordinates if school.district else None,
        communities=communities_data
    )

@router.post("/", response_model=SchoolResponse)
async def create_school(school: SchoolCreate, db: Session = Depends(get_db)):
    db_school = School(**school.model_dump())
    
    coords = await geocode_school(school.name, school.address)
    if coords:
        db_school.longitude, db_school.latitude = coords
    
    db.add(db_school)
    db.commit()
    db.refresh(db_school)
    return db_school

@router.put("/{school_id}", response_model=SchoolResponse)
async def update_school(school_id: int, school: SchoolUpdate, db: Session = Depends(get_db)):
    db_school = db.query(School).filter(School.id == school_id).first()
    if not db_school:
        raise HTTPException(status_code=404, detail="学校不存在")
    
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

@router.delete("/{school_id}")
def delete_school(school_id: int, db: Session = Depends(get_db)):
    db_school = db.query(School).filter(School.id == school_id).first()
    if not db_school:
        raise HTTPException(status_code=404, detail="学校不存在")
    
    db.delete(db_school)
    db.commit()
    return {"message": "删除成功"}
