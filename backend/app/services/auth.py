from passlib.context import CryptContext

from app.core.constants import PWD_SCHEME_BCRYPT

pwd_context = CryptContext(schemes=[PWD_SCHEME_BCRYPT], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
