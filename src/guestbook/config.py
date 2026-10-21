from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "guestbook"
    postgres_user: str = "guestbook"
    postgres_password: str  # обязательный, без значения по умолчанию — секрет не живёт в коде

    app_version: str = "dev"  # подставляется при сборке образа (build-arg APP_VERSION)

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
