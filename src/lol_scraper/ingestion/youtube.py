"""Thin wrapper around yt-dlp: fetch metadata/chapters and resolve a streamable format URL.

No video is downloaded here — `fetch_metadata` only pulls the info_dict, and
`resolve_stream_url` resolves a direct, seekable media URL that `video/frames.py`
hands to ffmpeg. Actual frame extraction lives in `video/frames.py`.
"""

from typing import Any

import yt_dlp

from lol_scraper.ingestion.schemas import Chapter, VideoMetadata


def _base_ydl_opts() -> dict[str, Any]:
    return {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }


def fetch_metadata(url: str) -> VideoMetadata:
    with yt_dlp.YoutubeDL(_base_ydl_opts()) as ydl:
        info = ydl.extract_info(url, download=False)

    chapters = [
        Chapter(
            title=c.get("title", ""),
            start_seconds=c["start_time"],
            end_seconds=c["end_time"],
        )
        for c in info.get("chapters") or []
    ]

    return VideoMetadata(
        video_id=info["id"],
        url=info.get("webpage_url", url),
        title=info.get("title", ""),
        channel=info.get("channel", info.get("uploader", "")),
        upload_date=info.get("upload_date"),
        duration_seconds=float(info.get("duration") or 0),
        chapters=chapters,
    )


def resolve_stream_url(url: str, *, format_selector: str = "best[ext=mp4]") -> str:
    """Resolve a direct, HTTP-range-seekable media URL for a given format.

    ffmpeg can then seek/extract frames from this URL directly (`-ss`/`-t`)
    without yt-dlp downloading the full video to disk.
    """
    opts = _base_ydl_opts() | {"format": format_selector}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if "url" in info:
            return info["url"]
        # format selector matched a specific format entry
        return info["requested_formats"][0]["url"]
