from pydantic import BaseModel


class Chapter(BaseModel):
    title: str
    start_seconds: float
    end_seconds: float


class VideoMetadata(BaseModel):
    video_id: str
    url: str
    title: str
    channel: str
    upload_date: str | None = None
    duration_seconds: float
    chapters: list[Chapter] = []
