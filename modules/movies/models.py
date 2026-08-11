# modules/movies/models.py
# Модель фильма. Специфична для модуля фильмов.

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Movie:
    """Фильм, который мы получили из API."""

    kinopoisk_id: int
    title: str
    type: str = "unknown"
    rating: float = 0.0
    votes: int = 0
    genres: List[str] = field(default_factory=list)
    description: str = ""
    poster_url: str = ""

    def display_genres(self, limit: int = 2) -> List[str]:
        """
        Возвращает только первые N жанров для отображения пользователю.

        Ты просил показывать только 2 жанра, хотя в базе храним все.
        Этот метод решает эту задачу.
        """
        return self.genres[:limit]

    def genres_as_text(self, limit: int = 2) -> str:
        """Жанры в виде строки через запятую."""
        return ", ".join(self.display_genres(limit))


if __name__ == "__main__":
    print("--- Тестируем модель Movie ---")
    movie = Movie(
        kinopoisk_id=123,
        title="Интерстеллар",
        rating=8.6,
        votes=500000,
        genres=["фантастика", "драма", "приключения", "детектив"],
    )
    print(f"Все жанры: {movie.genres}")
    print(f"Для показа (2): {movie.display_genres()}")
    print(f"Текстом: {movie.genres_as_text()}")