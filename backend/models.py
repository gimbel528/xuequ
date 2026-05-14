from sqlalchemy import Column, Integer, String, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from database import Base

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
