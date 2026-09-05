from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.constants import JWT_COOKIE_NAME, MSG_AUTH_REQUIRED, MSG_EMPLOYEE_REQUIRED, ROLE_EMPLOYEE
from app.db.session import get_db
from app.models.user import User
from app.services.security import decode_access_token


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Пользователь по JWT из httpOnly cookie. Переиспользуется защитой маршрутов (AUTH-007)."""
    token = request.cookies.get(JWT_COOKIE_NAME)
    user_id = decode_access_token(token) if token else None
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=MSG_AUTH_REQUIRED,
        )
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=MSG_AUTH_REQUIRED,
        )
    return user


def get_current_employee(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != ROLE_EMPLOYEE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=MSG_EMPLOYEE_REQUIRED,
        )
    return current_user