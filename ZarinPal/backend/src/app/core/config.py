from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BACKEND_DIR.parent / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = "development"
    app_name: str = "Full-stack Starter"
    debug: bool = False
    log_level: str = "INFO"
    database_url: str | None = None
    postgres_db: str = "app"
    postgres_user: str = "app"
    postgres_password: SecretStr = SecretStr("app")
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    secret_key: SecretStr = SecretStr("development-only-change-me")
    host: str = "0.0.0.0"
    port: int = 8000
    static_dir: Path = BACKEND_DIR / "static"

    @model_validator(mode="after")
    def assemble_database_url(self) -> Settings:
        if not self.database_url:
            password = self.postgres_password.get_secret_value()
            self.database_url = (
                f"postgresql+psycopg://{self.postgres_user}:{password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        return self

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
