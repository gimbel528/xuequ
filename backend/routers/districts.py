import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import District, School
from schemas import DistrictCreate, DistrictUpdate, DistrictResponse

router = APIRouter(prefix="/districts", tags=["districts"])

AMAP_WEB_KEY = "fa00396c785cea9ca43456e42fd099e6"

async def geocode_address(address: str, city: str = "大连") -> tuple[float, float] | None:
    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {
        "key": AMAP_WEB_KEY,
        "address": f"{city}{address}",
        "city": city
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()
        if data.get("status") == "1" and data.get("geocodes"):
            location = data["geocodes"][0].get("location")
            if location:
                lng, lat = location.split(",")
                return float(lng), float(lat)
    return None

def convex_hull(points: List[tuple[float, float]]) -> List[tuple[float, float]]:
    if len(points) < 3:
        return points
    
    points = sorted(points)
    
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    
    lower = []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    
    upper = []
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    
    return lower[:-1] + upper[:-1]

@router.get("/", response_model=List[DistrictResponse])
def get_districts(db: Session = Depends(get_db)):
    return db.query(District).all()

@router.get("/{district_id}", response_model=DistrictResponse)
def get_district(district_id: int, db: Session = Depends(get_db)):
    district = db.query(District).filter(District.id == district_id).first()
    if not district:
        raise HTTPException(status_code=404, detail="学区边界不存在")
    return district

@router.get("/school/{school_id}", response_model=DistrictResponse)
def get_district_by_school(school_id: int, db: Session = Depends(get_db)):
    district = db.query(District).filter(District.school_id == school_id).first()
    if not district:
        raise HTTPException(status_code=404, detail="该学校暂无学区边界")
    return district

@router.post("/", response_model=DistrictResponse)
def create_district(district: DistrictCreate, db: Session = Depends(get_db)):
    school = db.query(School).filter(School.id == district.school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")
    
    existing = db.query(District).filter(District.school_id == district.school_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="该学校已有学区边界，请使用更新接口")
    
    db_district = District(**district.model_dump())
    db.add(db_district)
    db.commit()
    db.refresh(db_district)
    return db_district

@router.post("/generate-from-communities")
async def generate_from_communities(
    school_id: int,
    communities: List[str],
    db: Session = Depends(get_db)
):
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")
    
    coordinates = []
    not_found = []
    
    for community in communities:
        community = community.strip()
        if not community:
            continue
        result = await geocode_address(community)
        if result:
            coordinates.append(result)
        else:
            not_found.append(community)
    
    if len(coordinates) < 3:
        raise HTTPException(
            status_code=400, 
            detail=f"找到的坐标点不足3个，无法生成边界。未找到的小区：{not_found}"
        )
    
    hull_points = convex_hull(coordinates)
    hull_coords = [[p[0], p[1]] for p in hull_points]
    coords_json = str(hull_coords)
    
    existing = db.query(District).filter(District.school_id == school_id).first()
    if existing:
        existing.coordinates = coords_json
        db.commit()
        db.refresh(existing)
        return {
            "message": "边界更新成功",
            "coordinates": hull_coords,
            "not_found": not_found,
            "total_found": len(coordinates)
        }
    else:
        db_district = District(school_id=school_id, coordinates=coords_json)
        db.add(db_district)
        db.commit()
        db.refresh(db_district)
        return {
            "message": "边界创建成功",
            "coordinates": hull_coords,
            "not_found": not_found,
            "total_found": len(coordinates)
        }

@router.put("/{district_id}", response_model=DistrictResponse)
def update_district(district_id: int, district: DistrictUpdate, db: Session = Depends(get_db)):
    db_district = db.query(District).filter(District.id == district_id).first()
    if not db_district:
        raise HTTPException(status_code=404, detail="学区边界不存在")
    
    db_district.coordinates = district.coordinates
    db.commit()
    db.refresh(db_district)
    return db_district

@router.put("/school/{school_id}", response_model=DistrictResponse)
def update_district_by_school(school_id: int, district: DistrictUpdate, db: Session = Depends(get_db)):
    db_district = db.query(District).filter(District.school_id == school_id).first()
    if not db_district:
        raise HTTPException(status_code=404, detail="该学校暂无学区边界")
    
    db_district.coordinates = district.coordinates
    db.commit()
    db.refresh(db_district)
    return db_district

@router.delete("/{district_id}")
def delete_district(district_id: int, db: Session = Depends(get_db)):
    db_district = db.query(District).filter(District.id == district_id).first()
    if not db_district:
        raise HTTPException(status_code=404, detail="学区边界不存在")
    
    db.delete(db_district)
    db.commit()
    return {"message": "删除成功"}

@router.delete("/school/{school_id}")
def delete_district_by_school(school_id: int, db: Session = Depends(get_db)):
    db_district = db.query(District).filter(District.school_id == school_id).first()
    if not db_district:
        raise HTTPException(status_code=404, detail="该学校暂无学区边界")
    
    db.delete(db_district)
    db.commit()
    return {"message": "删除成功"}
