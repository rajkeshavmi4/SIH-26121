from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    app_name: str = "WELLSAGE AI"
    app_version: str = "0.2.0"
    database_url: str = "sqlite:///./wellsage.db"
    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"
    lookahead_meters: float = 300.0
    max_upload_bytes: int = 10 * 1024 * 1024
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
settings = Settings()
