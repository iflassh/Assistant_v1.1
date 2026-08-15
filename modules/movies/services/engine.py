# modules/movies/services/engine.py
# Дирижёр сценария подбора фильмов.
# Теперь умеет работать с базой через репозитории (DI),
# но сам по-прежнему не пишет SQL.

from typing import List, Optional, Set
import logging

from core.database import Database
from core.models import User
from modules.movies.models import Movie
from modules.movies.config import MovieSettings
from modules.movies.client import MovieApiClient
from modules.movies.repository import MovieRepository
from modules.movies.services.filters import filter_movies
from modules.movies.services.preferences import (
    PreferenceStrategy,
    GenrePreferenceStrategy,
    TopRatedStrategy,
)

logger = logging.getLogger(__name__)


class MovieRecommendationEngine:
    """
    Подбор фильмов: API/кэш → фильтры → стратегия → топ-N.

    Зависимости получают снаружи (DI): настройки, клиент API,
    репозиторий фильмов и ядро базы.
    """

    def __init__(
        self,
        settings: MovieSettings,
        api_client: MovieApiClient,
        repository: MovieRepository,
        database: Database,
        default_strategy: Optional[PreferenceStrategy] = None,
    ):
        self._settings = settings
        self._api_client = api_client
        self._repo = repository
        self._db = database
        self._default_strategy = default_strategy or GenrePreferenceStrategy()
        self._fallback_strategy = TopRatedStrategy()

    # ------------------------------------------------------------------
    # Чистая логика подбора (без походов в базу)
    # ------------------------------------------------------------------

    def recommend(
        self,
        user: User,
        limit: int = 3,
        exclude_ids: Optional[Set[int]] = None,
    ) -> List[Movie]:
        """
        Подбирает топ-N фильмов для готового пользователя.

        exclude_ids — ID фильмов, которые показывать нельзя
        (например, уже показанные). База сюда не ходит:
        движок остаётся чистым и тестируемым.
        """
        raw_movies = self._fetch_movies()
        if not raw_movies:
            logger.warning("Нет фильмов ни из API, ни из кэша.")
            return []

        # Фильтр качества
        clean_movies = filter_movies(raw_movies, self._settings)

        # Исключаем уже показанные
        if exclude_ids:
            clean_movies = [
                m for m in clean_movies if m.kinopoisk_id not in exclude_ids
            ]

        if not clean_movies:
            logger.warning("После фильтров и исключений фильмов не осталось.")
            return []

        # Основная стратегия, при сбое — запасная
        try:
            recommendations = self._default_strategy.pick(
                clean_movies, user, limit=limit
            )
            if recommendations:
                return recommendations
        except Exception as e:
            logger.error(f"Ошибка основной стратегии: {e}. Берём запасную.")

        return self._fallback_strategy.pick(clean_movies, user, limit=limit)

    # ------------------------------------------------------------------
    # «Взрослый» метод: полный сценарий с базой
    # ------------------------------------------------------------------

    def recommend_for_user(self, vk_id: int, limit: int = 3) -> List[Movie]:
        """
        Полный сценарий для конкретного пользователя VK:
        1. собираем пользователя из двух владельцев (ядро + модуль);
        2. подбираем, исключая показанные;
        3. отмечаем рекомендованное как показанное.
        """
        # 1. Пользователь: база из ядра, жанры из репозитория модуля
        self._db.ensure_user(vk_id)
        user = self._db.get_user(vk_id)
        user.preferred_genres = self._repo.get_user_genres(vk_id)

        # 2. История показов → исключаем
        shown = self._repo.get_shown_ids(vk_id)
        recommendations = self.recommend(user, limit=limit, exclude_ids=shown)

        # 3. Что рекомендовали — считаем показанным
        if recommendations:
            self._repo.mark_movies_shown(
                vk_id, [m.kinopoisk_id for m in recommendations]
            )

        return recommendations

    # ------------------------------------------------------------------
    # Источники данных с деградацией
    # ------------------------------------------------------------------

    def _fetch_movies(self, limit: int = 50) -> List[Movie]:
        """
        Сначала пробуем API. Если API недоступен —
        gracefully degradation: берём кэш каталога из БД.
        """
        try:
            movies = self._api_client.fetch_movies(limit=limit)
            # Успех из API — заодно кэшируем в БД
            # (задел под будущую стратегию «весь каталог»)
            for m in movies:
                self._repo.save_movie(m)
            return movies
        except Exception as e:
            logger.warning(f"API недоступен ({e}). Иду в кэш каталога.")
            return self._repo.get_catalog(limit=limit)


# --- Тестовый блок: полный сценарий без реального API ---
if __name__ == "__main__":
    import os

    logging.basicConfig(level=logging.INFO)

    TEST_DB = "test_engine_db.sqlite"
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    # Фундамент + репозиторий (порядок важен!)
    db = Database(TEST_DB)
    repo = MovieRepository(db.connection)

    settings = MovieSettings(
        min_rating=6.5, min_votes=100, movies_per_day=3,
        api_key="test", base_url="test",
    )
    # fetch_movies у клиента ещё заглушка → движок уйдёт в кэш
    client = MovieApiClient(settings)

    # Наполняем кэш каталога, как будто API раньше работал
    catalog = [
        Movie(kinopoisk_id=1, title="Интерстеллар", rating=8.6, votes=500000, genres=["фантастика", "драма"]),
        Movie(kinopoisk_id=2, title="Дюна", rating=8.0, votes=300000, genres=["фантастика", "приключения"]),
        Movie(kinopoisk_id=3, title="Супер-комедия", rating=9.0, votes=400000, genres=["комедия"]),
        Movie(kinopoisk_id=4, title="Прибытие", rating=7.9, votes=250000, genres=["фантастика", "драма"]),
    ]
    for m in catalog:
        repo.save_movie(m)

    # Пользователь любит фантастику
    db.ensure_user(1)
    repo.set_user_genres(1, ["фантастика"])

    engine = MovieRecommendationEngine(settings, client, repo, db)

    first = engine.recommend_for_user(1, limit=2)
    print("Первая подборка:", [m.title for m in first])

    second = engine.recommend_for_user(1, limit=2)
    print("Вторая подборка (показанные исключены):", [m.title for m in second])

    db.close()
    os.remove(TEST_DB)
    print("✓ Engine с базой работает")