from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://lol_scraper:lol_scraper@localhost:5432/lol_scraper"

    data_dir: Path = Path("data")
    frames_dir: Path = Path("data/frames")
    processed_dir: Path = Path("data/processed")

    ocr_provider: str = "easyocr"
    frame_interval_seconds: float = 10.0

    log_level: str = "INFO"


settings = Settings()
