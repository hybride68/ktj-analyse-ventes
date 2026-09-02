import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from backend import models
    from backend.database import Base, engine, ensure_schema
    from backend.routers import auth, imports, kpis, rfm, previsions
except ImportError:
    import models
    from database import Base, engine, ensure_schema
    from routers import auth, imports, kpis, rfm, previsions

app = FastAPI(title="Projet PME API")


def _parse_allowed_origins() -> list[str]:
    raw_value = os.getenv("ALLOWED_ORIGINS", "*").strip()
    if not raw_value or raw_value == "*":
        return ["*"]
    return [origin.strip() for origin in raw_value.split(",") if origin.strip()]


allow_origins = _parse_allowed_origins()
allow_credentials = allow_origins != ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def create_tables() -> None:
    ensure_schema()


@app.get("/")
def read_root() -> dict:
    return {"message": "API PME opérationnelle"}


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(imports.router, prefix="/imports", tags=["imports"])
app.include_router(kpis.router, prefix="/kpis", tags=["kpis"])
app.include_router(rfm.router, prefix="/rfm", tags=["rfm"])
app.include_router(previsions.router, prefix="/previsions", tags=["previsions"])


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    reload_flag = os.getenv("ENV", "development").lower() == "development"
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=reload_flag)
