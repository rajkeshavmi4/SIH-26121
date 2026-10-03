from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    app_name: str = "Namowell AI"
    app_version: str = "1.0.0"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./namowell.db")
    cors_origins: str = "*"
    log_level: str = "INFO"
    lookahead_meters: float = 300.0
    max_upload_bytes: int = 25 * 1024 * 1024
    secret_key: str = "namowell-secret-key-change-in-prod"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

settings = Settings()
