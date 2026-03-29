from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str = "medivault-documents"
    minio_secure: bool = False

    # Auth0
    auth0_domain: str
    auth0_audience: str

    # Encryption key (AES-256, base64-encoded 32 bytes)
    encryption_key: str

    # Notifications
    sendgrid_api_key: str = ""

    # App
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:5173"]

    # Rate limiting
    rate_limit_auth: int = 10       # requests per minute per IP
    rate_limit_upload: int = 20     # requests per minute per user
    rate_limit_passport: int = 60   # requests per minute per IP


settings = Settings()  # type: ignore[call-arg]
