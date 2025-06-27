from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers.flags import router as flags_router
from app.internal.database import engine
from app.internal.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(flags_router, prefix="/flags", tags=["Flags"])


@app.get("/")
async def read_root():
    return {"message": "Feature Flag Service is running!"}
