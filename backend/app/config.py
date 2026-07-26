from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    debug: bool = True
    sqlite_path: Path = Field(default=Path("db.sqlite3"))
    media_root: Path = Field(default=Path("media"))
    page_size: int = 50

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.sqlite_path.as_posix()}"


settings = Settings()
