"""Configuração central da aplicação, carregada a partir de variáveis de ambiente."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    app_debug: bool = True
    app_secret_key: str = "insecure-dev-secret-change-me"
    app_base_url: str = "http://localhost:8000"
    app_allowed_origins: str = "http://localhost:8000"

    database_url: str = "sqlite+aiosqlite:///./triade.db"
    database_url_sync: str = "sqlite:///./triade.db"

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    supabase_storage_bucket: str = "attachments"

    oauth_redirect_url: str = "http://localhost:8000/auth/callback"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_oauth_redirect_url: str = "http://localhost:8000/integrations/google/callback"
    google_token_encryption_key: str = ""

    session_cookie_name: str = "triade_session"
    session_cookie_secure: bool = False
    csrf_cookie_name: str = "triade_csrf"

    rate_limit_default: str = "100/minute"
    rate_limit_auth: str = "10/minute"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.app_allowed_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
