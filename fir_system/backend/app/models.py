"""
app/models.py
ORM table definition + all Pydantic schemas in one place.
"""

from __future__ import annotations
from typing import List, Optional
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from pydantic import BaseModel

from fir_system.app.database import Base


# ─────────────────────────────────────────────────────────────
#  SQLAlchemy  ORM  model
# ─────────────────────────────────────────────────────────────

class FIRRecord(Base):
    __tablename__ = "fir_records"

    id          = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # complainant
    c_name      = Column(String(200),  nullable=True)
    c_phone     = Column(String(20),   nullable=True)
    c_address   = Column(Text,         nullable=True)
    # incident
    i_type      = Column(String(100),  nullable=True)
    i_date      = Column(String(30),   nullable=True)
    i_time      = Column(String(30),   nullable=True)
    i_location  = Column(Text,         nullable=True)
    i_desc      = Column(Text,         nullable=True)
    # suspect
    s_info      = Column(Text,         nullable=True)
    # arrays stored as JSON
    evidence        = Column(JSON,     nullable=True, default=list)
    objects_stolen  = Column(JSON,     nullable=True, default=list)
    # metadata
    reported_at = Column(DateTime,    default=datetime.utcnow)
    status      = Column(String(50),  default="pending")


# ─────────────────────────────────────────────────────────────
#  Pydantic  schemas
# ─────────────────────────────────────────────────────────────

class Complainant(BaseModel):
    name:    str = ""
    phone:   str = ""
    address: str = ""


class Incident(BaseModel):
    type:        str = ""
    date:        str = ""
    time:        str = ""
    location:    str = ""
    description: str = ""


class Suspect(BaseModel):
    info: str = ""


class Metadata(BaseModel):
    reported_at: str = ""
    status:      str = "pending"


class FIRSchema(BaseModel):
    complainant:    Complainant
    incident:       Incident
    suspect:        Suspect
    evidence:       List[str] = []
    objects_stolen: List[str] = []
    metadata:       Metadata


class FIRSaveRequest(BaseModel):
    """Body sent by frontend when user clicks Save."""
    complainant:    Complainant
    incident:       Incident
    suspect:        Suspect
    evidence:       List[str] = []
    objects_stolen: List[str] = []


class FIRListItem(BaseModel):
    id:          int
    c_name:      Optional[str]
    i_type:      Optional[str]
    i_date:      Optional[str]
    i_location:  Optional[str]
    status:      Optional[str]
    reported_at: Optional[str]

    class Config:
        from_attributes = True


class FIRDetail(BaseModel):
    id:             int
    complainant:    Complainant
    incident:       Incident
    suspect:        Suspect
    evidence:       List[str]
    objects_stolen: List[str]
    metadata:       Metadata
