from fastapi import FastAPI
from app.routers.flags import router as flags_router

app = FastAPI()

app.include_router(flags_router, prefix="/flags", tags=["Flags"])


@app.get("/")
async def read_root():
    return {"message": "Feature Flag Service is running!"}
