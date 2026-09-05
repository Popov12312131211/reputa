from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.constants import COOKIE_NAME, MSG_NOT_AUTHENTICATED
from app.db.session import get_db
from app.models.user import User
from app.services.auth import decode_access_token


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Возвращает текущего пользователя по JWT из httpOnly-cookie либо 401."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=MSG_NOT_AUTHENTICATED,
        )

    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=MSG_NOT_AUTHENTICATED,
        )

    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=MSG_NOT_AUTHENTICATED,
        )

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=MSG_NOT_AUTHENTICATED,
        )

    return user