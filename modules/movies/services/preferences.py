# modules/movies/services/preferences.py
# Стратегии подбора фильмов под вкусы пользователя.

from abc import ABC, abstractmethod
from typing import List
from modules.movies.models import Movie, MoviePreferences

#from core.models import User удалить
from modules.movies.models import Movie


class PreferenceStrategy(ABC):
    """
    Контракт (розетка) для всех стратегий подбора.
    Любая стратегия обязана уметь метод pick().
    """

    @abstractmethod
    def pick(self, movies: List[Movie], preferences: MoviePreferences, limit: int = 3) -> List[Movie]:
        """Выбирает лучшие фильмы для конкретного пользователя."""


class GenrePreferenceStrategy(PreferenceStrategy):
    #user_genres = set(preferences.preferred_genres)

    def pick(self, movies: List[Movie], preferences: MoviePreferences, limit: int = 3) -> List[Movie]:
        user_genres = set(preferences.preferred_genres)

        # Graceful degradation: если у пользователя ещё нет жанров,
        # не падаем, а просто показываем лучшее по рейтингу.
        if not user_genres:
            return sorted(movies, key=lambda m: m.rating, reverse=True)[:limit]

        def score(movie: Movie):
            # Сколько жанров фильма совпадает с любимыми жанрами пользователя
            matches = len(set(movie.genres) & user_genres)
            # Сортируем: сначала по совпадениям, потом по рейтингу, потом по голосам
            return (matches, movie.rating, movie.votes)

        ranked = sorted(movies, key=score, reverse=True)
        return ranked[:limit]


class TopRatedStrategy(PreferenceStrategy):
    """Запасная стратегия: просто самые рейтинговые фильмы."""

    def pick(self, movies: List[Movie], preferences: MoviePreferences, limit: int = 3) -> List[Movie]:
        return sorted(movies, key=lambda m: (m.rating, m.votes), reverse=True)[:limit]


if __name__ == "__main__":
    print("--- Тестируем стратегии ---")

    preferences = MoviePreferences(
        preferred_genres=["фантастика", "драма"]
    )

    #m1 = Movie(kinopoisk_id=1, title="Интерстеллар", rating=8.6, votes=500000, genres=["фантастика", "драма"])
    #m2 = Movie(kinopoisk_id=2, title="Супер-комедия", rating=9.0, votes=400000, genres=["комедия"])
    #m3 = Movie(kinopoisk_id=3, title="Дюна", rating=8.0, votes=300000, genres=["фантастика", "приключения"])

    m1 = Movie(kinopoisk_id=1, title="A", rating=7.6, votes=1000, genres=["фантастика", "драма"])
    m2 = Movie(kinopoisk_id=2, title="B", rating=9.0, votes=5000, genres=["фантастика"])
    m3 = Movie(kinopoisk_id=3, title="C", rating=7.5, votes=3000, genres=["фантастика", "драма"])

    strategy = GenrePreferenceStrategy()
    result = strategy.pick([m1, m2, m3], preferences, limit=3)

    for movie in result:
        print(f"  {movie.title}")