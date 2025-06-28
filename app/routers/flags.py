from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session, joinedload
from app.dependencies import get_db
from app.internal.models import Flag
from app.internal.schemas import FlagBody, FlagResponse, NestedFlagResponse
from app.internal.service import create_flag_service, toggle_flag_service, flag_to_response, get_flag_by_id_service, flag_to_nested_response

router = APIRouter()

@router.get("/", response_model=list[FlagResponse])
def read_flags(db: Session = Depends(get_db)):
    flags = db.query(Flag).options(joinedload(Flag.dependencies)).all()
    return [flag_to_response(flag) for flag in flags]


@router.get("/{flag_id}", response_model=NestedFlagResponse)
def get_flag_by_id(flag_id: int, db: Session = Depends(get_db)):
    flag = get_flag_by_id_service(flag_id, db)
    return flag_to_nested_response(flag)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=FlagResponse)
def create_flag(flag_in: FlagBody, db: Session = Depends(get_db)):
    new_flag = create_flag_service(flag_in, db)
    return flag_to_response(new_flag)

@router.patch("/toggle/{flag_id}", response_model=FlagResponse)
def toggle_flag(flag_id: int, db: Session = Depends(get_db)):
    flag_db = toggle_flag_service(flag_id, db)
    return flag_to_response(flag_db)
