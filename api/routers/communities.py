from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Community, School
from schemas import CommunityCreate, CommunityUpdate, CommunityResponse

router = APIRouter(prefix="/communities", tags=["communities"])

@router.get("/school/{school_id}", response_model=List[CommunityResponse])
def get_communities_by_school(school_id: int, db: Session = Depends(get_db)):
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")
    
    return db.query(Community).filter(Community.school_id == school_id).all()

@router.post("/", response_model=CommunityResponse)
def create_community(community: CommunityCreate, school_id: int, db: Session = Depends(get_db)):
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="学校不存在")
    
    db_community = Community(
        school_id=school_id,
        name=community.name,
        coordinates=community.coordinates
    )
    db.add(db_community)
    db.commit()
    db.refresh(db_community)
    return db_community

@router.put("/{community_id}", response_model=CommunityResponse)
def update_community(community_id: int, community: CommunityUpdate, db: Session = Depends(get_db)):
    db_community = db.query(Community).filter(Community.id == community_id).first()
    if not db_community:
        raise HTTPException(status_code=404, detail="小区不存在")
    
    update_data = community.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_community, key, value)
    
    db.commit()
    db.refresh(db_community)
    return db_community

@router.delete("/{community_id}")
def delete_community(community_id: int, db: Session = Depends(get_db)):
    db_community = db.query(Community).filter(Community.id == community_id).first()
    if not db_community:
        raise HTTPException(status_code=404, detail="小区不存在")
    
    db.delete(db_community)
    db.commit()
    return {"message": "删除成功"}
