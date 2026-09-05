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
from app.routers.applications import router as applications_router
from app.routers.employee import router as employee_router
from app.services.auth import decode_access_token

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(auth_router)
app.include_router(applications_router)
app.include_router(employee_router)

# Роли, которым разрешены приватные префиксы.
# Guard на уровне middleware избавляет каждый будущий роутер
# от ручного добавления проверки JWT.
_PRIVATE_PREFIX_ROLES = {
    "/user/": ROLE_USER,
    "/employee/": ROLE_EMPLOYEE,
}


def _required_role(path: str) -> str | None:
    # Голые префиксы тоже считаем приватными, а похожие пути
    # вроде /username — нет, поэтому сравниваем границу маршрута.
    for prefix, role in _PRIVATE_PREFIX_ROLES.items():
        if path == prefix[:-1] or path.startswith(prefix):
            return role
    return None


@app.middleware("http")
async def protect_private_routes(request: Request, call_next):
    required_role = _required_role(request.url.path)
    if required_role is not None:
        token = request.cookies.get(COOKIE_NAME)
        payload = decode_access_token(token) if token else None
        if payload is None or payload.get("role") != required_role:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": MSG_NOT_AUTHENTICATED},
            )
    return await call_next(request)


@app.get("/health")
def health():
    db_ok = check_db_connection()
    return {"status": "ok" if db_ok else "error", "database": "connected" if db_ok else "disconnected"}
