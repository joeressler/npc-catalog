from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Known insecure example values — refused when DEBUG=false.
INSECURE_AUTH_USERNAME = "admin"
INSECURE_AUTH_PASSWORD = "admin"
INSECURE_AUTH_SECRET = "dev-secret-change-me"
INSECURE_AUTH_PLAYER_USERNAME = "player"
INSECURE_AUTH_PLAYER_PASSWORD = "test"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    debug: bool = True
    sqlite_path: Path = Field(default=Path("db.sqlite3"))
    media_root: Path = Field(default=Path("media"))
    page_size: int = 50
    auth_username: str = Field(default=INSECURE_AUTH_USERNAME)
    auth_password: str = Field(default=INSECURE_AUTH_PASSWORD)
    auth_player_username: str = Field(default=INSECURE_AUTH_PLAYER_USERNAME)
    auth_player_password: str = Field(default=INSECURE_AUTH_PLAYER_PASSWORD)
    auth_secret: str = Field(default=INSECURE_AUTH_SECRET)
    auth_cookie_secure: bool = False
    # ComfyUI image generation (Docker production). Off by default for split-dev.
    comfyui_enabled: bool = False
    comfyui_url: str = ""
    comfyui_timeout_seconds: int = 180

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.sqlite_path.as_posix()}"

    @property
    def comfyui_configured(self) -> bool:
        return self.comfyui_enabled and bool(self.comfyui_url.strip())


def validate_production_secrets(cfg: Settings | None = None) -> None:
    """Refuse to start with empty or example credentials when DEBUG is off."""
    cfg = cfg or settings
    if cfg.debug:
        return

    problems: list[str] = []
    username = cfg.auth_username.strip()
    password = cfg.auth_password.strip()
    player_username = cfg.auth_player_username.strip()
    player_password = cfg.auth_player_password.strip()
    secret = cfg.auth_secret.strip()

    if not username:
        problems.append("AUTH_USERNAME is empty")
    elif username == INSECURE_AUTH_USERNAME:
        problems.append("AUTH_USERNAME is the insecure example value")

    if not password:
        problems.append("AUTH_PASSWORD is empty")
    elif password == INSECURE_AUTH_PASSWORD:
        problems.append("AUTH_PASSWORD is the insecure example value")

    if not player_username:
        problems.append("AUTH_PLAYER_USERNAME is empty")
    elif player_username == INSECURE_AUTH_PLAYER_USERNAME and player_password == INSECURE_AUTH_PLAYER_PASSWORD:
        problems.append("AUTH_PLAYER_USERNAME/AUTH_PLAYER_PASSWORD are the insecure example values")

    if not player_password:
        problems.append("AUTH_PLAYER_PASSWORD is empty")
    elif player_password == INSECURE_AUTH_PLAYER_PASSWORD:
        problems.append("AUTH_PLAYER_PASSWORD is the insecure example value")

    if username and player_username and username == player_username:
        problems.append("AUTH_USERNAME and AUTH_PLAYER_USERNAME must differ")

    if not secret:
        problems.append("AUTH_SECRET is empty")
    elif secret == INSECURE_AUTH_SECRET:
        problems.append("AUTH_SECRET is the insecure example value")

    if problems:
        detail = "; ".join(problems)
        raise RuntimeError(
            f"Refusing to start with DEBUG=false and insecure auth config: {detail}. "
            "Set strong unique AUTH_USERNAME, AUTH_PASSWORD, AUTH_PLAYER_USERNAME, "
            "AUTH_PLAYER_PASSWORD, and AUTH_SECRET."
        )


settings = Settings()
