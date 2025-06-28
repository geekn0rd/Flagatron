from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.dependencies import get_db
from app.internal.models import Flag
from app.internal.schemas import FlagBody, FlagResponse

router = APIRouter()

@router.get("/", response_model=list[FlagResponse])
def read_flags(db: Session = Depends(get_db)):
    flags = db.query(Flag).all()
    return flags

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=FlagResponse)
def create_flag(flag_in: FlagBody, db: Session = Depends(get_db)):
    # Check for duplicate flag name
    existing = db.query(Flag).filter(Flag.name == flag_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Flag with this name already exists.")

    new_flag = Flag(name=flag_in.name)

    if flag_in.dependencies:
        deps = db.query(Flag).filter(Flag.id.in_(flag_in.dependencies)).all()
        if len(deps) != len(flag_in.dependencies):
            raise HTTPException(status_code=400, detail="One or more dependencies not found.")
        new_flag.dependencies = deps

    db.add(new_flag)
    db.commit()
    db.refresh(new_flag)
    return new_flag

@router.patch("/toggle/{flag_id}", response_model=FlagResponse)
def toggle_flag(flag_id: int, db: Session = Depends(get_db)):
    flag_db = db.query(Flag).filter(Flag.id == flag_id).first()
    if not flag_db:
        raise HTTPException(status_code=404, detail="Flag not found.")
    flag_db.is_active = not flag_db.is_active

    db.commit()
    db.refresh(flag_db)
    return flag_db
