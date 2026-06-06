import app.models  # noqa: F401
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import Base, engine
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Workflow Automation", lifespan=lifespan)
app.include_router(router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Workflow system running"}
