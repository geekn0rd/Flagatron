from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI
from fastapi.params import Depends
from sqlmodel import Session

from app.internal.database import SessionLocal
from app.routers.flags import router as flags_router


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()


app = FastAPI(lifespan=lifespan)

app.include_router(flags_router, prefix="/flags", tags=["Flags"])


@app.get("/")
async def read_root():
    return {"message": "Feature Flag Service is running!"}
