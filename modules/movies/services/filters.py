# modules/movies/services/filters.py
# Сортировочная линия для фильмов.
# Здесь только чистые функции, которые проверяют качество фильмов.

from typing import List
from modules.movies.models import Movie
from modules.movies.config import MovieSettings


def is_good_quality(movie: Movie, settings: MovieSettings) -> bool:
    """
    Проверяет, проходит ли фильм базовые фильтры качества.

    Возвращает True, если фильм достоин показа.
    Возвращает False, если фильм нужно отбросить.
    """
    # 1. Фильтр по рейтингу
    if movie.rating < settings.min_rating:
        return False

    # 2. Фильтр по количеству голосов
    if movie.votes < settings.min_votes:
        return False

    # Если дошли до сюда — фильм прошел все проверки
    return True


def has_genres(movie: Movie) -> bool:
    """
    Дополнительная проверка: есть ли у фильма вообще жанры.
    Иногда API присылает фильмы без жанров, их показывать нельзя.
    """
    return bool(movie.genres)


def filter_movies(movies: List[Movie], settings: MovieSettings) -> List[Movie]:
    """
    Главный метод модуля.
    Берет кучу сырых фильмов и возвращает только хорошие.
    """
    good_movies = []

    for movie in movies:
        if is_good_quality(movie, settings) and has_genres(movie):
            good_movies.append(movie)

    return good_movies


# --- Блок для локальной проверки (запускай прямо этот файл) ---
if __name__ == "__main__":
    print("--- Тестируем фильтры ---")

    # Создаем фейковые настройки
    fake_settings = MovieSettings(
        min_rating=6.5,
        min_votes=100,
        movies_per_day=3,
        api_key="test",
        base_url="test"
    )

    # Создаем 3 тестовых фильма
    movie_1 = Movie(kinopoisk_id=1, title="Хороший фильм", rating=8.0, votes=5000, genres=["драма"])
    movie_2 = Movie(kinopoisk_id=2, title="Плохой рейтинг", rating=4.0, votes=5000, genres=["комедия"])  # Отсеется
    movie_3 = Movie(kinopoisk_id=3, title="Мало голосов", rating=9.0, votes=5, genres=["ужасы"])  # Отсеется

    raw_movies = [movie_1, movie_2, movie_3]

    # Применяем фильтр
    result = filter_movies(raw_movies, fake_settings)

    print(f"Было фильмов: {len(raw_movies)}")
    print(f"Стало фильмов: {len(result)}")
    if result:
        print(f"Остался только: {result[0].title}")