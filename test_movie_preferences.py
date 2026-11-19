from modules.movies.models import Movie, MoviePreferences
from modules.movies.services.preferences import GenrePreferenceStrategy

def test_genre_strategy_without_preferences():
    preferences = MoviePreferences()
    m1 = Movie(kinopoisk_id=1, title="A", rating=7.6, votes=1000, genres=["фантастика", "драма"])
    m2 = Movie(kinopoisk_id=2, title="B", rating=9.0, votes=5000, genres=["фантастика"])
    m3 = Movie(kinopoisk_id=3, title="C", rating=7.5, votes=3000, genres=["фантастика", "драма"])
    strategy = GenrePreferenceStrategy()
    result = strategy.pick([m1, m2, m3], preferences, limit=2)
    titles = [movie.title for movie in result]
    assert titles == ["B", "A"], f"Неожиданный порядок фильмов: {titles}"

def test_genre_strategy_order_and_limit():
    preferences = MoviePreferences(
        preferred_genres=["фантастика", "драма"]
    )
    m1 = Movie(kinopoisk_id=1, title="A", rating=7.6, votes=1000, genres=["фантастика", "драма"])
    m2 = Movie(kinopoisk_id=2, title="B", rating=9.0, votes=5000, genres=["фантастика"])
    m3 = Movie(kinopoisk_id=3, title="C", rating=7.5, votes=3000, genres=["фантастика", "драма"])
    strategy = GenrePreferenceStrategy()
    result = strategy.pick([m1, m2, m3], preferences, limit=2)
    titles = [movie.title for movie in result]
    assert titles == ["A", "C"], f"Неожиданный порядок фильмов: {titles}"




if __name__ == "__main__":
    test_genre_strategy_order_and_limit()
    test_genre_strategy_without_preferences()
    print("Проверка стратегии пройдена")