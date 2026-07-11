from fastapi import FastAPI

from backend import models
from backend.database import Base, engine
from backend.routers import auth, kpis, rfm, previsions

app = FastAPI(title="Projet PME API")


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/")
def read_root() -> dict:
    return {"message": "API PME opérationnelle"}


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(kpis.router, prefix="/kpis", tags=["kpis"])
app.include_router(rfm.router, prefix="/rfm", tags=["rfm"])
app.include_router(previsions.router, prefix="/previsions", tags=["previsions"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
