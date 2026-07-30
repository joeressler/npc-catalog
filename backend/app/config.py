from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    debug: bool = True
    sqlite_path: Path = Field(default=Path("db.sqlite3"))
    media_root: Path = Field(default=Path("media"))
    page_size: int = 50
    auth_username: str = Field(default="admin")
    auth_password: str = Field(default="admin")
    auth_secret: str = Field(default="dev-secret-change-me")
    auth_cookie_secure: bool = False

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.sqlite_path.as_posix()}"


settings = Settings()
