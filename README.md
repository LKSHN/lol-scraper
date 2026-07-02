# lol-scraper

Collects competitive League of Legends data (LEC/LCS/etc.) by scraping broadcast
VODs on YouTube. Uses `yt-dlp` to read video metadata/chapters and to stream video
frames directly into `ffmpeg` (no full VOD is downloaded to disk), reads the
in-game HUD via OCR, and stores structured stats in Postgres for later
analysis/graphing.

## Pipeline

```
YouTube URL
  -> ingestion   (yt-dlp: metadata, chapters, resolve a streamable format URL)
  -> video       (ffmpeg samples frames at an interval, straight from the stream URL)
  -> ocr         (crop HUD regions per frame, OCR them — EasyOCR by default)
  -> extraction  (raw OCR text -> typed GameSnapshot, via postprocess cleanup)
  -> storage     (SQLAlchemy models -> Postgres: matches, games, teams, snapshots)
```

Each stage lives in its own module under `src/lol_scraper/` and can be run/tested
independently; `pipeline/run.py` wires them together, and `cli.py` exposes them.

## Requirements

- Python 3.12+, [uv](https://docs.astral.sh/uv/)
- `ffmpeg` on PATH (frame extraction)
- Docker (for the local Postgres instance)

## Setup

```bash
uv sync
cp .env.example .env

./scripts/dev_up.sh        # starts Postgres via docker compose + runs migrations
```

## CLI

```bash
# Fetch metadata + chapters for a VOD (no download)
uv run lolscraper ingest "<youtube-url>"

# Debug: extract sampled frames from a time range into data/frames/<video_id>/
uv run lolscraper frames "<youtube-url>" --start 0 --end 120 --interval 10

# Full pipeline for one game within a VOD
uv run lolscraper pipeline-run "<youtube-url>" \
  --league LEC --blue-team "G2 Esports" --red-team "Fnatic" \
  --start 0 --end 1800
```

## Development

```bash
uv run pytest
uv run ruff check .
uv run mypy src
```

New migration after changing `storage/models.py`:

```bash
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```

## Status / known gaps

This is an initial scaffold, not a working scraper yet:

- **HUD regions are placeholders** (`video/regions.py`) — need calibrating against
  real broadcast frames per league/production (LEC vs LCS vs LPL layouts differ).
- **`video/frames.py`** extracts frames straight from a resolved stream URL; the
  approach (seek-on-URL vs pipe) needs validating against a real long-form VOD —
  some formats/CDNs don't support HTTP range seeking well.
- **No per-player extraction yet** — only team-level gold/clock are wired end to
  end; KDA, CS, items, and champion identification (likely template matching
  rather than OCR) are follow-up work.
- **No automatic game-boundary detection** — `pipeline-run` takes an explicit
  `--start/--end` for one game; using YouTube chapters to auto-split a VOD into
  games is not yet implemented (see `ingestion.schemas.Chapter`, already fetched
  by `ingest`).
- **EasyOCR pulls in PyTorch** (~GB of deps). If that's too heavy, swapping in
  Tesseract or PaddleOCR only requires adding a new `OCRProvider` implementation
  (see `ocr/base.py`) — nothing else changes.
