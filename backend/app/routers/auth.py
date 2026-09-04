from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import (
    MSG_USER_ALREADY_EXISTS,
    MSG_INVALID_CREDENTIALS,
)
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
)
from app.services.auth import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.login == body.login).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=MSG_USER_ALREADY_EXISTS,
        )

    user = User(
        full_name=body.full_name,
        birth_date=body.birth_date,
        login=body.login,
        password_hash=hash_password(body.password),
        phone=body.phone,
        telegram=body.telegram,
        role=UserRole.USER.value,
    )
    # Гонка двух параллельных запросов с одним логином ловится здесь:
    # pre-check выше её не видит, unique-ограничение в БД — видит.
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=MSG_USER_ALREADY_EXISTS,
        ) from exc

    return user


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.login == body.login).first()
    # Один и тот же ответ для несуществующего логина и неверного пароля,
    # чтобы не раскрывать наличие аккаунта по коду/сообщению.
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=MSG_INVALID_CREDENTIALS,
        )

    token = create_access_token(user)
    response.set_cookie(
        key=settings.ACCESS_TOKEN_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/",
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
    )
    return user
