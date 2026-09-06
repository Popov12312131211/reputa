from pydantic_settings import BaseSettings

from app.core.constants import COOKIE_NAME


class Settings(BaseSettings):
    PROJECT_NAME: str = "Reputa"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/reputa"
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 часа
    # Единый источник имени cookie — constants.COOKIE_NAME (AUTH-007).
    # Его же читают get_current_user и middleware, поэтому set/read не разойдутся.
    ACCESS_TOKEN_COOKIE_NAME: str = COOKIE_NAME
    COOKIE_SECURE: bool = False  # включать True только за HTTPS

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
