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

# Full pipeline for one explicit game window within a VOD
uv run lolscraper pipeline-run "<youtube-url>" \
  --league LEC --blue-team "G2 Esports" --red-team "Fnatic" \
  --start 0 --end 1800

# Full pipeline for every game in a VOD, auto-detected from YouTube chapters
# titled "Game 1", "Game 2", ... (raises if the VOD has no such chapters)
uv run lolscraper pipeline-run-match "<youtube-url>" \
  --league LEC --blue-team "G2 Esports" --red-team "Fnatic"
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

Validated end-to-end against a real VOD (MSI 2026 Play-Ins, T1 vs Team Liquid
Alienware): ingestion, 1080p frame streaming (video-only stream, no download),
HUD regions calibrated against the "LoL Esports" broadcast overlay, OCR
(clock + team gold, with a per-region character allowlist and a plausibility
guard on gold readings), idempotent storage, and chapter-based multi-game
splitting.

- **HUD regions** (`video/regions.py`) are calibrated against one specific
  production ("LoL Esports" MSI overlay) — LEC/LCS/LPL and other productions
  use different overlays and still need their own calibration pass.
- **No per-player extraction yet** — only team-level gold/clock are wired end to
  end; KDA, CS, items, and champion identification (likely template matching
  rather than OCR) are follow-up work.
- **Chapter-based game detection assumes chapters titled "Game N"** (see
  `pipeline/chapters.py`) — matches every broadcast VOD checked so far, but a
  production that titles chapters differently (e.g. "Map 1") won't be detected.
  It also assumes blue/red side stays constant across every detected game,
  which doesn't hold when teams swap sides between games in a Bo3/Bo5.
- **EasyOCR pulls in PyTorch** (~GB of deps). If that's too heavy, swapping in
  Tesseract or PaddleOCR only requires adding a new `OCRProvider` implementation
  (see `ocr/base.py`) — nothing else changes.
