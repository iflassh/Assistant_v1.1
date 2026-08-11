# modules/movies/config.py
# Настройки МОДУЛЯ ФИЛЬМОВ.
# Здесь только то, что касается подбора фильмов.

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class MovieSettings:
    """Настройки модуля подбора фильмов."""

    # --- Фильтрация ---
    min_rating: float = 6.5
    min_votes: int = 100

    # --- Поведение ---
    movies_per_day: int = 3

    # --- API ---
    api_key: str = ""
    base_url: str = "https://api.poiskkino.dev/v1.5"


def load_movie_settings() -> MovieSettings:
    """Читает настройки модуля фильмов из .env."""
    return MovieSettings(
        min_rating=float(os.getenv("MIN_RATING", "6.5")),
        min_votes=int(os.getenv("MIN_VOTES", "100")),
        movies_per_day=int(os.getenv("MOVIES_PER_DAY", "3")),
        api_key=os.getenv("POISK_KINO_API_KEY", "").strip(),
        base_url=os.getenv("POISK_KINO_BASE_URL", "https://api.poiskkino.dev/v1.5").strip(),
    )


if __name__ == "__main__":
    print("--- Тестируем настройки модуля фильмов ---")
    settings = load_movie_settings()
    print("✓ Настройки модуля фильмов загружены!")
    print(f"  Мин. рейтинг: {settings.min_rating}")
    print(f"  Мин. голоса: {settings.min_votes}")
    print(f"  Фильмов в день: {settings.movies_per_day}")
    print(f"  API URL: {settings.base_url}")