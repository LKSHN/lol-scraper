from lol_scraper.ingestion.schemas import Chapter
from lol_scraper.pipeline.chapters import detect_games


def _chapter(title: str, start: float, end: float) -> Chapter:
    return Chapter(title=title, start_seconds=start, end_seconds=end)


def test_detect_games_filters_non_game_chapters():
    chapters = [
        _chapter("Intro", 0, 120),
        _chapter("Pregame Show", 120, 600),
        _chapter("Game 1", 600, 2400),
        _chapter("Post-game Interview", 2400, 2700),
        _chapter("Game 2", 2700, 4500),
        _chapter("Analysis Desk", 4500, 5000),
    ]

    games = detect_games(chapters)

    assert [g.game_number for g in games] == [1, 2]
    assert games[0].start_seconds == 600
    assert games[0].end_seconds == 2400
    assert games[1].start_seconds == 2700
    assert games[1].end_seconds == 4500


def test_detect_games_returns_empty_when_no_chapters():
    assert detect_games([]) == []


def test_detect_games_returns_empty_when_no_game_chapters():
    chapters = [_chapter("Intro", 0, 120), _chapter("Highlights", 120, 300)]
    assert detect_games(chapters) == []


def test_detect_games_tolerates_casing_and_spacing():
    chapters = [
        _chapter("GAME1", 0, 100),
        _chapter("game 2", 100, 200),
        _chapter("Game   3", 200, 300),
    ]

    games = detect_games(chapters)

    assert [g.game_number for g in games] == [1, 2, 3]


def test_detect_games_orders_by_number_not_chapter_position():
    # a misc chapter (e.g. a delayed VOD upload with a caster segment spliced
    # in) shouldn't throw off game ordering, since it's driven by the number
    # in each chapter's own title.
    chapters = [
        _chapter("Game 2", 100, 200),
        _chapter("Caster Segment", 200, 250),
        _chapter("Game 1", 0, 100),
    ]

    games = detect_games(chapters)

    assert [g.game_number for g in games] == [1, 2]
