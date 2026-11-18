"""
app/routes.py
All REST endpoints:
  POST /api/extract      → upload audio → FIR preview JSON
  POST /api/fir          → save edited FIR to MySQL
  GET  /api/fir          → list all saved FIRs
  GET  /api/fir/{id}     → get single FIR detail
  PUT  /api/fir/{id}     → update a saved FIR
  DELETE /api/fir/{id}   → delete a FIR
"""

import os
import shutil
import tempfile
from datetime import datetime
from typing import List

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session

from fir_system.app.database  import get_db
from fir_system.app.ml_models import get
from fir_system.app.pipeline  import run as run_pipeline
from fir_system.app.models    import (
    FIRRecord, FIRSchema, FIRSaveRequest,
    FIRListItem, FIRDetail,
    Complainant, Incident, Suspect, Metadata,
)

router = APIRouter()

ALLOWED_EXT = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".webm"}


# ── POST /api/extract  (audio → preview JSON, no DB write) ───────────────────
@router.post("/api/extract", response_model=FIRSchema, tags=["NLP"])
async def extract_fir(
    file: UploadFile = File(..., description="Audio complaint file"),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"Unsupported file type '{ext}'.")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        ml  = get()
        fir = run_pipeline(ml, tmp_path)
        return fir

    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


# ── POST /api/fir  (save to MySQL) ────────────────────────────────────────────
@router.post("/api/fir", tags=["FIR"])
def save_fir(body: FIRSaveRequest, db: Session = Depends(get_db)):
    rec = FIRRecord(
        c_name      = body.complainant.name,
        c_phone     = body.complainant.phone,
        c_address   = body.complainant.address,
        i_type      = body.incident.type,
        i_date      = body.incident.date,
        i_time      = body.incident.time,
        i_location  = body.incident.location,
        i_desc      = body.incident.description,
        s_info      = body.suspect.info,
        evidence        = body.evidence,
        objects_stolen  = body.objects_stolen,
        reported_at = datetime.utcnow(),
        status      = "pending",
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {"id": rec.id, "message": "FIR saved successfully."}


# ── GET /api/fir  (list all) ──────────────────────────────────────────────────
@router.get("/api/fir", response_model=List[FIRListItem], tags=["FIR"])
def list_firs(db: Session = Depends(get_db)):
    rows = db.query(FIRRecord).order_by(FIRRecord.reported_at.desc()).all()
    result = []
    for r in rows:
        result.append(FIRListItem(
            id          = r.id,
            c_name      = r.c_name,
            i_type      = r.i_type,
            i_date      = r.i_date,
            i_location  = r.i_location,
            status      = r.status,
            reported_at = r.reported_at.strftime("%Y-%m-%d %H:%M") if r.reported_at else "",
        ))
    return result


# ── GET /api/fir/{id}  (detail) ───────────────────────────────────────────────
@router.get("/api/fir/{fir_id}", response_model=FIRDetail, tags=["FIR"])
def get_fir(fir_id: int, db: Session = Depends(get_db)):
    r = db.query(FIRRecord).filter(FIRRecord.id == fir_id).first()
    if not r:
        raise HTTPException(404, "FIR not found.")
    return _to_detail(r)


# ── PUT /api/fir/{id}  (update) ───────────────────────────────────────────────
@router.put("/api/fir/{fir_id}", tags=["FIR"])
def update_fir(fir_id: int, body: FIRSaveRequest, db: Session = Depends(get_db)):
    r = db.query(FIRRecord).filter(FIRRecord.id == fir_id).first()
    if not r:
        raise HTTPException(404, "FIR not found.")

    r.c_name         = body.complainant.name
    r.c_phone        = body.complainant.phone
    r.c_address      = body.complainant.address
    r.i_type         = body.incident.type
    r.i_date         = body.incident.date
    r.i_time         = body.incident.time
    r.i_location     = body.incident.location
    r.i_desc         = body.incident.description
    r.s_info         = body.suspect.info
    r.evidence       = body.evidence
    r.objects_stolen = body.objects_stolen

    db.commit()
    return {"message": "FIR updated successfully."}


# ── DELETE /api/fir/{id} ──────────────────────────────────────────────────────
@router.delete("/api/fir/{fir_id}", tags=["FIR"])
def delete_fir(fir_id: int, db: Session = Depends(get_db)):
    r = db.query(FIRRecord).filter(FIRRecord.id == fir_id).first()
    if not r:
        raise HTTPException(404, "FIR not found.")
    db.delete(r)
    db.commit()
    return {"message": "FIR deleted."}


# ── Helper ────────────────────────────────────────────────────────────────────
def _to_detail(r: FIRRecord) -> FIRDetail:
    return FIRDetail(
        id          = r.id,
        complainant = Complainant(
            name=r.c_name or "", phone=r.c_phone or "", address=r.c_address or ""
        ),
        incident    = Incident(
            type=r.i_type or "", date=r.i_date or "",
            time=r.i_time or "", location=r.i_location or "",
            description=r.i_desc or "",
        ),
        suspect        = Suspect(info=r.s_info or ""),
        evidence        = r.evidence or [],
        objects_stolen  = r.objects_stolen or [],
        metadata        = Metadata(
            reported_at = r.reported_at.strftime("%Y-%m-%d %H:%M:%S") if r.reported_at else "",
            status      = r.status or "pending",
        ),
    )
