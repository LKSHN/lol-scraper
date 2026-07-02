from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    league: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    players: Mapped[list["Player"]] = relationship(back_populates="team")


class Player(Base):
    __tablename__ = "players"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"), index=True)
    ign: Mapped[str] = mapped_column(String)  # in-game name
    role: Mapped[str | None] = mapped_column(String, nullable=True)

    team: Mapped[Team] = relationship(back_populates="players")


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    video_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    league: Mapped[str] = mapped_column(String, index=True)
    title: Mapped[str] = mapped_column(String)

    games: Mapped[list["Game"]] = relationship(back_populates="match", cascade="all, delete-orphan")


class Game(Base):
    __tablename__ = "games"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    match_id: Mapped[str] = mapped_column(ForeignKey("matches.id"), index=True)
    game_number: Mapped[int] = mapped_column(Integer)
    blue_team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"))
    red_team_id: Mapped[str] = mapped_column(ForeignKey("teams.id"))
    start_seconds: Mapped[float] = mapped_column(Float)
    end_seconds: Mapped[float] = mapped_column(Float)

    match: Mapped[Match] = relationship(back_populates="games")
    blue_team: Mapped[Team] = relationship(foreign_keys=[blue_team_id])
    red_team: Mapped[Team] = relationship(foreign_keys=[red_team_id])
    snapshots: Mapped[list["Snapshot"]] = relationship(
        back_populates="game", cascade="all, delete-orphan"
    )


class Snapshot(Base):
    """A single time-series stat reading (one OCR'd frame) for a game."""

    __tablename__ = "snapshots"
    __table_args__ = (
        # Re-running the pipeline over a game it already processed (or an
        # overlapping --start/--end window) must not duplicate readings.
        # video_timestamp_seconds -- the frame's offset into the source video
        # -- is known deterministically from the extraction request, not
        # OCR'd, so unlike game_clock_seconds it's never NULL and is safe to
        # use as the dedup key. frame_path isn't safe either: ffmpeg numbers
        # frames frame_000001.jpg, frame_000002.jpg... from 1 on every run,
        # so the same filename can refer to a different in-game moment across
        # runs. See repository.add_snapshot for the upsert.
        UniqueConstraint(
            "game_id", "video_timestamp_seconds", name="uq_snapshot_game_video_timestamp"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[str] = mapped_column(ForeignKey("games.id"), index=True)
    frame_path: Mapped[str] = mapped_column(String)
    video_timestamp_seconds: Mapped[float] = mapped_column(Float)
    game_clock_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    blue_gold: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blue_kills: Mapped[int | None] = mapped_column(Integer, nullable=True)
    blue_towers: Mapped[int | None] = mapped_column(Integer, nullable=True)

    red_gold: Mapped[int | None] = mapped_column(Integer, nullable=True)
    red_kills: Mapped[int | None] = mapped_column(Integer, nullable=True)
    red_towers: Mapped[int | None] = mapped_column(Integer, nullable=True)

    game: Mapped[Game] = relationship(back_populates="snapshots")
