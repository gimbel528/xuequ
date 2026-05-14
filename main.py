from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import httpx

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

# 内存数据存储
schools_data = []
communities_data = []
next_school_id = 1
next_community_id = 1

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

class SchoolWithDistrict(SchoolResponse):
    has_district: bool = False
    coordinates: Optional[str] = None
    communities: List[CommunityResponse] = []

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
def get_schools():
    result = []
    for school in schools_data:
        school_communities = [c for c in communities_data if c["school_id"] == school["id"]]
        school_data = SchoolWithDistrict(
            id=school["id"],
            name=school["name"],
            address=school["address"],
            phone=school["phone"],
            description=school["description"],
            color=school["color"],
            longitude=school["longitude"],
            latitude=school["latitude"],
            has_district=len(school_communities) > 0,
            coordinates=None,
            communities=[CommunityResponse(**c) for c in school_communities]
        )
        result.append(school_data)
    return result

@app.get("/api/schools/{school_id}", response_model=SchoolWithDistrict)
def get_school(school_id: int):
    school = next((s for s in schools_data if s["id"] == school_id), None)
    if not school:
        raise Exception("学校不存在")
    school_communities = [c for c in communities_data if c["school_id"] == school_id]
    return SchoolWithDistrict(
        id=school["id"],
        name=school["name"],
        address=school["address"],
        phone=school["phone"],
        description=school["description"],
        color=school["color"],
        longitude=school["longitude"],
        latitude=school["latitude"],
        has_district=len(school_communities) > 0,
        coordinates=None,
        communities=[CommunityResponse(**c) for c in school_communities]
    )

@app.post("/api/schools", response_model=SchoolResponse)
async def create_school(school: SchoolCreate):
    global next_school_id
    school_dict = school.model_dump()
    school_dict["id"] = next_school_id
    school_dict["longitude"] = None
    school_dict["latitude"] = None
    coords = await geocode_school(school.name, school.address)
    if coords:
        school_dict["longitude"], school_dict["latitude"] = coords
    schools_data.append(school_dict)
    next_school_id += 1
    return SchoolResponse(**school_dict)

@app.put("/api/schools/{school_id}", response_model=SchoolResponse)
async def update_school(school_id: int, school: SchoolUpdate):
    school_idx = next((i for i, s in enumerate(schools_data) if s["id"] == school_id), None)
    if school_idx is None:
        raise Exception("学校不存在")
    update_data = school.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        schools_data[school_idx][key] = value
    if (school.name or school.address) and school.longitude is None and school.latitude is None:
        name = school.name or schools_data[school_idx]["name"]
        address = school.address if school.address else schools_data[school_idx]["address"]
        coords = await geocode_school(name, address)
        if coords:
            schools_data[school_idx]["longitude"], schools_data[school_idx]["latitude"] = coords
    return SchoolResponse(**schools_data[school_idx])

@app.delete("/api/schools/{school_id}")
def delete_school(school_id: int):
    global schools_data, communities_data
    school_idx = next((i for i, s in enumerate(schools_data) if s["id"] == school_id), None)
    if school_idx is None:
        raise Exception("学校不存在")
    schools_data.pop(school_idx)
    communities_data = [c for c in communities_data if c["school_id"] != school_id]
    return {"message": "删除成功"}

# Communities Routes
@app.get("/api/communities/school/{school_id}", response_model=List[CommunityResponse])
def get_communities_by_school(school_id: int):
    school = next((s for s in schools_data if s["id"] == school_id), None)
    if not school:
        raise Exception("学校不存在")
    return [CommunityResponse(**c) for c in communities_data if c["school_id"] == school_id]

@app.post("/api/communities", response_model=CommunityResponse)
def create_community(community: CommunityCreate, school_id: int):
    global next_community_id
    school = next((s for s in schools_data if s["id"] == school_id), None)
    if not school:
        raise Exception("学校不存在")
    community_dict = community.model_dump()
    community_dict["id"] = next_community_id
    community_dict["school_id"] = school_id
    communities_data.append(community_dict)
    next_community_id += 1
    return CommunityResponse(**community_dict)

@app.put("/api/communities/{community_id}", response_model=CommunityResponse)
def update_community(community_id: int, community: CommunityUpdate):
    community_idx = next((i for i, c in enumerate(communities_data) if c["id"] == community_id), None)
    if community_idx is None:
        raise Exception("小区不存在")
    update_data = community.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        communities_data[community_idx][key] = value
    return CommunityResponse(**communities_data[community_idx])

@app.delete("/api/communities/{community_id}")
def delete_community(community_id: int):
    global communities_data
    community_idx = next((i for i, c in enumerate(communities_data) if c["id"] == community_id), None)
    if community_idx is None:
        raise Exception("小区不存在")
    communities_data.pop(community_idx)
    return {"message": "删除成功"}
