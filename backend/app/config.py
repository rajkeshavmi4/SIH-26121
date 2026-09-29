from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    database_url: str = "sqlite:///./wellsage.db"
    cors_origins: str = "http://localhost:5173"
    lookahead_meters: float = 300.0
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    @property
    def origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]
settings = Settings()
