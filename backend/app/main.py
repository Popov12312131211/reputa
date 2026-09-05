from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.constants import (
    COOKIE_NAME,
    MSG_NOT_AUTHENTICATED,
    ROLE_EMPLOYEE,
    ROLE_USER,
)
from app.db.session import check_db_connection
from app.routers.auth import router as auth_router
from app.services.auth import decode_access_token

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(auth_router)

# Роли, которым разрешены приватные префиксы.
# Guard на уровне middleware избавляет каждый будущий роутер
# от ручного добавления проверки JWT.
_PRIVATE_PREFIX_ROLES = {
    "/user/": ROLE_USER,
    "/employee/": ROLE_EMPLOYEE,
}


@app.middleware("http")
async def protect_private_routes(request: Request, call_next):
    for prefix, required_role in _PRIVATE_PREFIX_ROLES.items():
        if request.url.path.startswith(prefix):
            token = request.cookies.get(COOKIE_NAME)
            payload = decode_access_token(token) if token else None
            if payload is None or payload.get("role") != required_role:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": MSG_NOT_AUTHENTICATED},
                )
            break
    return await call_next(request)


@app.get("/health")
def health():
    db_ok = check_db_connection()
    return {"status": "ok" if db_ok else "error", "database": "connected" if db_ok else "disconnected"}
