from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Reputa"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/reputa"
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 часа
    ACCESS_TOKEN_COOKIE_NAME: str = "access_token"
    COOKIE_SECURE: bool = False  # включать True только за HTTPS

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
