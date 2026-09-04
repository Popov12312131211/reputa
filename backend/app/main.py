from fastapi import FastAPI

from app.core.config import settings
from app.db.session import check_db_connection

app = FastAPI(title=settings.PROJECT_NAME)


@app.get("/health")
def health():
    db_ok = check_db_connection()
    return {"status": "ok" if db_ok else "error", "database": "connected" if db_ok else "disconnected"}
