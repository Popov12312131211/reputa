from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import (
    MSG_USER_ALREADY_EXISTS,
    MSG_INVALID_CREDENTIALS,
    MSG_INVALID_STAFF_CODE,
    MSG_NOT_EMPLOYEE,
    STAFF_LOGIN_CODE,
)
from app.db.session import get_db
from app.models.user import User, UserRole
from app.routers.deps import get_current_user
from app.schemas.auth import (
    MeResponse,
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    EmployeeLoginRequest,
)
from app.services.auth import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookie(response: Response, user: User) -> None:
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


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.login == body.login).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=MSG_USER_ALREADY_EXISTS,
        )

    # Первый зарегистрированный пользователь в пустой БД становится сотрудником:
    # так сотрудники заводятся на демо без отдельного админ-интерфейса.
    role = UserRole.USER.value
    if db.query(User).count() == 0:
        role = UserRole.EMPLOYEE.value

    user = User(
        full_name=body.full_name,
        birth_date=body.birth_date,
        login=body.login,
        password_hash=hash_password(body.password),
        phone=body.phone,
        telegram=body.telegram,
        role=role,
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


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
  
  
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

    _set_auth_cookie(response, user)
    return user


@router.post("/login/employee", response_model=LoginResponse)
def employee_login(body: EmployeeLoginRequest, response: Response, db: Session = Depends(get_db)):
    if body.code != STAFF_LOGIN_CODE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=MSG_INVALID_STAFF_CODE,
        )

    user = db.query(User).filter(User.login == body.login).first()
    # Код проверяется выше и для несуществующего логина, и для неверного пароля
    # отвечаем одинаково, аналогично обычному входу.
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=MSG_INVALID_CREDENTIALS,
        )

    if user.role != UserRole.EMPLOYEE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=MSG_NOT_EMPLOYEE,
        )

    _set_auth_cookie(response, user)
    return user
