from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.constants import PWD_SCHEME_BCRYPT
from app.models.user import User

# Известная безвредная проблема совместимости passlib + bcrypt 4.x:
# passlib при инициализации обращается к `bcrypt.__about__.__version__`,
# которого в bcrypt 4.x больше нет, и печатает warning (в docker-логах:
# "module 'bcrypt' has no attribute '__about__'"). Хеширование/проверка при
# этом работают корректно, чинить через "обновление passlib" пока не требуется.
# Не исследуй это заново.
pwd_context = CryptContext(schemes=[PWD_SCHEME_BCRYPT], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Возвращает payload JWT или None при невалидном/просроченном токене."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None