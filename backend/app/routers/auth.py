from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.constants import MSG_USER_ALREADY_EXISTS
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest, RegisterResponse
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest
from app.services.auth import hash_password

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


@router.get("/profile", response_model=ProfileResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/profile", response_model=ProfileResponse)
def update_profile(
    body: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    duplicate = (
        db.query(User)
        .filter(User.login == body.login, User.id != current_user.id)
        .first()
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=MSG_USER_ALREADY_EXISTS,
        )

    current_user.full_name = body.full_name
    current_user.login = body.login
    current_user.phone = body.phone
    current_user.telegram = body.telegram
    if body.password is not None:
        current_user.password_hash = hash_password(body.password)

    try:
        db.commit()
        db.refresh(current_user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=MSG_USER_ALREADY_EXISTS,
        ) from exc

    return current_user
