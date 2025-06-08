from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.dependencies import get_session

router = APIRouter()

@router.get("/")
def read_flags(session: Session = Depends(get_session)):
    # Example usage of the session
    return {"message": "This endpoint uses a database session from the router."} 