import os
from typing import List, Optional, Union
from pydantic_settings import BaseSettings, SettingsConfigDict

# Guarantee pure-Python fallback for SQLAlchemy C-extensions to avoid Windows Application Control / AppLocker .pyd blocks
os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"


class Settings(BaseSettings):
    PROJECT_NAME: str = "Evanta OS"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "postgresql+psycopg://postgres:9948496652pp@localhost:5432/evanta_os"
    SECRET_KEY: str = "evanta_os_secure_jwt_secret_token_hyderabad_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"

    # Single Station Configuration: Hyderabad, Telangana, India
    STATION_CODE: str = "PRABHU-HYD-01"
    STATION_NAME: str = "Prabhu's Grid"
    STATION_OWNER: str = "Prabhu"
    STATION_CITY: str = "Hyderabad"
    STATION_STATE: str = "Telangana"
    STATION_COUNTRY: str = "India"
    DEFAULT_ADDRESS: str = "HITEC City / Madhapur Corridor, Hyderabad, Telangana 500081, India"
    DEFAULT_TARIFF: float = 18.5  # ₹ / kWh
    DEMO_MODE: bool = True
    DATA_SOURCE_LABEL: str = "SIMULATED_DEMO_SOURCE"

    # Email / SMTP Configuration for password resets
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@evanta.os"

    # Development-only authentication bypass (strictly prohibited in production)
    DEV_AUTH_BYPASS: bool = False

    @property
    def is_dev_auth_bypass_enabled(self) -> bool:
        if self.ENVIRONMENT.lower() in ("production", "prod"):
            return False
        return bool(self.DEV_AUTH_BYPASS)

    @property
    def is_email_configured(self) -> bool:
        return bool(self.SMTP_HOST and self.SMTP_HOST.strip())

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        if isinstance(self.CORS_ORIGINS, str):
            origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
            if origins:
                return origins
        # Fallback to explicit localhost origins (never wildcard * with credentials)
        return [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
