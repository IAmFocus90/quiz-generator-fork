from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    VERIFICATION_TOKEN_EXPIRE_HOURS: int = 2
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENABLE_TEST_USER_ROUTES: bool = False
    ENABLE_PUBLIC_USER_LIST: bool = False

    email_sender: str
    email_password: str
    email_host: str
    email_port: int
    share_url: str
    db_name: str
    mongo_url: str
    QUIZ_V2_WRITE_MODE: Literal["legacy_only", "dual_write"] = "dual_write"
    QUIZ_V2_FAIL_OPEN: bool = True
    QUIZ_V2_STRUCTURED_LOGGING: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
