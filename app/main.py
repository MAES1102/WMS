import app.models  # noqa: F401
from fastapi import FastAPI

from app.db import Base, engine
from app.routes import router

app = FastAPI(title="Workflow Automation")
app.include_router(router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Workflow system running"}


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
