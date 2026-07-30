from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Known insecure example values — refused when DEBUG=false.
INSECURE_AUTH_USERNAME = "admin"
INSECURE_AUTH_PASSWORD = "admin"
INSECURE_AUTH_SECRET = "dev-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    debug: bool = True
    sqlite_path: Path = Field(default=Path("db.sqlite3"))
    media_root: Path = Field(default=Path("media"))
    page_size: int = 50
    auth_username: str = Field(default=INSECURE_AUTH_USERNAME)
    auth_password: str = Field(default=INSECURE_AUTH_PASSWORD)
    auth_secret: str = Field(default=INSECURE_AUTH_SECRET)
    auth_cookie_secure: bool = False

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.sqlite_path.as_posix()}"


def validate_production_secrets(cfg: Settings | None = None) -> None:
    """Refuse to start with empty or example credentials when DEBUG is off."""
    cfg = cfg or settings
    if cfg.debug:
        return

    problems: list[str] = []
    username = cfg.auth_username.strip()
    password = cfg.auth_password.strip()
    secret = cfg.auth_secret.strip()

    if not username:
        problems.append("AUTH_USERNAME is empty")
    elif username == INSECURE_AUTH_USERNAME:
        problems.append("AUTH_USERNAME is the insecure example value")

    if not password:
        problems.append("AUTH_PASSWORD is empty")
    elif password == INSECURE_AUTH_PASSWORD:
        problems.append("AUTH_PASSWORD is the insecure example value")

    if not secret:
        problems.append("AUTH_SECRET is empty")
    elif secret == INSECURE_AUTH_SECRET:
        problems.append("AUTH_SECRET is the insecure example value")

    if problems:
        detail = "; ".join(problems)
        raise RuntimeError(
            f"Refusing to start with DEBUG=false and insecure auth config: {detail}. "
            "Set strong unique AUTH_USERNAME, AUTH_PASSWORD, and AUTH_SECRET."
        )


settings = Settings()
