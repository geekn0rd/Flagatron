from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.dependencies import get_db
from app.internal.models import Flag
from app.internal.schemas import FlagBase, FlagInDB

router = APIRouter()

@router.get("/", response_model=list[FlagInDB])
def read_flags(session: Session = Depends(get_db)):
    flags = session.execute(select(Flag)).scalars().all()
    return flags

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=FlagBase)
def create_flag(flag_in: FlagBase, session: Session = Depends(get_db)):
    # Check for duplicate flag name
    existing = session.execute(select(Flag).where(Flag.name == flag_in.name)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Flag with this name already exists.")

    new_flag = Flag(name=flag_in.name, is_active=flag_in.is_active)

    if flag_in.dependencies:
        deps = session.execute(
            select(Flag).where(Flag.id.in_(flag_in.dependencies))
        ).scalars().all()
        if len(deps) != len(flag_in.dependencies):
            raise HTTPException(status_code=400, detail="One or more dependencies not found.")
        new_flag.dependencies = deps

    session.add(new_flag)
    session.commit()
    session.refresh(new_flag)
    return new_flag
