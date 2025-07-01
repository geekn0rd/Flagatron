from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from app.dependencies import get_db
from app.internal.models import Flag, AuditLog
from app.internal.schemas import FlagBody, FlagResponse, NestedFlagResponse, AuditLogResponse
from app.internal.service import (
    create_flag_service, 
    toggle_flag_service, 
    flag_to_response, 
    get_flag_by_id_service, 
    flag_to_nested_response,
    get_audit_logs_service
)

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
def create_flag(
    flag_in: FlagBody, 
    db: Session = Depends(get_db),
    actor: Optional[str] = Query(None, description="Actor performing the operation")
):
    new_flag = create_flag_service(flag_in, db, actor=actor)
    return flag_to_response(new_flag)

@router.patch("/toggle/{flag_id}", response_model=FlagResponse)
def toggle_flag(
    flag_id: int, 
    db: Session = Depends(get_db),
    actor: Optional[str] = Query(None, description="Actor performing the operation")
):
    flag_db = toggle_flag_service(flag_id, db, actor=actor)
    return flag_to_response(flag_db)


# Audit logs endpoints
@router.get("/audit-logs/", response_model=list[AuditLogResponse])
def get_audit_logs(
    db: Session = Depends(get_db),
    flag_id: Optional[int] = Query(None, description="Filter by flag ID"),
    operation: Optional[str] = Query(None, description="Filter by operation type"),
    actor: Optional[str] = Query(None, description="Filter by actor"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return"),
    offset: int = Query(0, ge=0, description="Number of logs to skip")
):
    """
    Retrieve audit logs with optional filtering.
    """
    audit_logs = get_audit_logs_service(
        db=db,
        flag_id=flag_id,
        operation=operation,
        actor=actor,
        limit=limit,
        offset=offset
    )
    return audit_logs
