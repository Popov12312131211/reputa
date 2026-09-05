from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.constants import COOKIE_NAME, MSG_NOT_AUTHENTICATED
from app.db.session import get_db
from app.models.user import User
from app.services.auth import decode_access_token


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=MSG_NOT_AUTHENTICATED,
    )


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Возвращает текущего пользователя по JWT из httpOnly-cookie либо 401."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise _unauthorized()

    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise _unauthorized()

    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise _unauthorized() from None

    user = db.get(User, user_id)
    if user is None:
        raise _unauthorized()

    return user