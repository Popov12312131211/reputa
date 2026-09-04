from fastapi import FastAPI

from app.core.config import settings
from app.db.session import check_db_connection
from app.routers.auth import router as auth_router

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(auth_router)


@app.get("/health")
def health():
    db_ok = check_db_connection()
    return {"status": "ok" if db_ok else "error", "database": "connected" if db_ok else "disconnected"}
