"""Frame extraction via ffmpeg, streamed directly from a resolved yt-dlp media URL.

No intermediate video file is written to disk: ffmpeg seeks/reads straight from
the HTTP(S) stream URL produced by `ingestion.youtube.resolve_stream_url` and
writes sampled frames as images.
"""

import shutil
import subprocess
from pathlib import Path

from lol_scraper.logging_conf import get_logger

logger = get_logger(__name__)


class FfmpegNotFoundError(RuntimeError):
    pass


def extract_frames(
    stream_url: str,
    out_dir: Path,
    *,
    start_seconds: float = 0.0,
    end_seconds: float | None = None,
    interval_seconds: float = 10.0,
) -> list[Path]:
    """Extract one frame every `interval_seconds` between start/end into `out_dir`.

    Returns the list of written frame paths, ordered by timestamp.
    """
    if shutil.which("ffmpeg") is None:
        raise FfmpegNotFoundError("ffmpeg not found on PATH")

    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in out_dir.glob("frame_*.jpg"):
        stale.unlink()
    pattern = out_dir / "frame_%06d.jpg"

    cmd = ["ffmpeg", "-y", "-ss", str(start_seconds)]
    if end_seconds is not None:
        cmd += ["-to", str(end_seconds)]
    cmd += [
        "-i", stream_url,
        "-vf", f"fps=1/{interval_seconds}",
        "-q:v", "2",
        str(pattern),
    ]

    logger.info("extract_frames.start", cmd=" ".join(cmd))
    subprocess.run(cmd, check=True, capture_output=True)

    frames = sorted(out_dir.glob("frame_*.jpg"))
    logger.info("extract_frames.done", count=len(frames))
    return frames
