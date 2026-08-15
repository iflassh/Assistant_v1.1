# modules/movies/repository.py
# Репозиторий модуля фильмов: ЕДИНСТВЕННЫЙ класс, пишущий SQL
# по кино-таблицам.
#
# Владеет таблицами (префикс/смысл — «кино»):
#   movie_user_genres — любимые жанры пользователя (кино-предпочтения)
#   movies            — кэш фильмов из API (жанры как JSON)
#   user_shown_movies — история показов
#   user_waiting_list — «посмотрю позже»
#
# Подключение НЕ открывает сам — получает его от core.Database (DI).

import json
import sqlite3
from typing import List, Optional, Set

from modules.movies.models import Movie


class MovieRepository:
    """Весь SQL модуля фильмов в одном месте."""

    def __init__(self, conn: sqlite3.Connection):
        # Переиспользуем подключение ядра — одно на всё приложение.
        self._conn = conn
        self._init_schema()

    def _init_schema(self) -> None:
        """
        Создаёт таблицы модуля.

        Порядок создания в main.py важен: сначала Database (users),
        потом MovieRepository — таблицы ссылаются на users.
        """
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS movie_user_genres (
                vk_id INTEGER NOT NULL REFERENCES users(vk_id),
                genre TEXT NOT NULL,
                PRIMARY KEY (vk_id, genre)
            );

            CREATE TABLE IF NOT EXISTS movies (
                kinopoisk_id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                type TEXT DEFAULT 'unknown',
                rating REAL DEFAULT 0.0,
                votes INTEGER DEFAULT 0,
                genres TEXT DEFAULT '[]',
                description TEXT DEFAULT '',
                poster_url TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS user_shown_movies (
                vk_id INTEGER NOT NULL REFERENCES users(vk_id),
                kinopoisk_id INTEGER NOT NULL REFERENCES movies(kinopoisk_id),
                shown_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (vk_id, kinopoisk_id)
            );

            CREATE TABLE IF NOT EXISTS user_waiting_list (
                vk_id INTEGER NOT NULL REFERENCES users(vk_id),
                kinopoisk_id INTEGER NOT NULL REFERENCES movies(kinopoisk_id),
                added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (vk_id, kinopoisk_id)
            );
            """
        )

    #Метод добавлен
    def get_catalog(self, limit: int = 50) -> List[Movie]:
        """
        Возвращает кэш фильмов из БД (запасной источник, если API упал).
        Сортируем по рейтингу — пусть запасной вариант будет достойным.
        """
        rows = self._conn.execute(
            "SELECT * FROM movies ORDER BY rating DESC, votes DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [self._row_to_movie(r) for r in rows]
    
    # ------------------------------------------------------------------
    # Предпочтения пользователя (жанры)
    # ------------------------------------------------------------------

    def get_user_genres(self, vk_id: int) -> List[str]:
        """Любимые жанры пользователя для модуля фильмов."""
        rows = self._conn.execute(
            "SELECT genre FROM movie_user_genres WHERE vk_id = ? ORDER BY genre",
            (vk_id,),
        ).fetchall()
        return [r["genre"] for r in rows]

    def set_user_genres(self, vk_id: int, genres: List[str]) -> None:
        """
        Полностью заменяет жанры пользователя.
        Ожидает, что пользователь уже создан ядром (db.ensure_user).
        """
        with self._conn:  # транзакция: delete+insert атомарны
            self._conn.execute(
                "DELETE FROM movie_user_genres WHERE vk_id = ?", (vk_id,)
            )
            self._conn.executemany(
                "INSERT INTO movie_user_genres (vk_id, genre) VALUES (?, ?)",
                [(vk_id, g) for g in genres],
            )

    # ------------------------------------------------------------------
    # Кэш фильмов
    # ------------------------------------------------------------------

    def _upsert_movie(self, movie: Movie) -> None:
        """Сохраняет или обновляет фильм (INSERT OR REPLACE)."""
        self._conn.execute(
            """
            INSERT OR REPLACE INTO movies
                (kinopoisk_id, title, type, rating, votes,
                 genres, description, poster_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                movie.kinopoisk_id,
                movie.title,
                movie.type,
                movie.rating,
                movie.votes,
                # ensure_ascii=False — чтобы «фантастика» хранилась читаемо
                json.dumps(movie.genres, ensure_ascii=False),
                movie.description,
                movie.poster_url,
            ),
        )

    def save_movie(self, movie: Movie) -> None:
        with self._conn:
            self._upsert_movie(movie)

    def _row_to_movie(self, row) -> Movie:
        """Переводит строку таблицы в модель Movie."""
        return Movie(
            kinopoisk_id=row["kinopoisk_id"],
            title=row["title"],
            type=row["type"],
            rating=row["rating"],
            votes=row["votes"],
            genres=json.loads(row["genres"]),
            description=row["description"],
            poster_url=row["poster_url"],
        )

    def get_movie(self, kinopoisk_id: int) -> Optional[Movie]:
        row = self._conn.execute(
            "SELECT * FROM movies WHERE kinopoisk_id = ?", (kinopoisk_id,)
        ).fetchone()
        return self._row_to_movie(row) if row is not None else None

    # ------------------------------------------------------------------
    # История показов
    # ------------------------------------------------------------------

    def get_shown_ids(self, vk_id: int) -> Set[int]:
        """ID фильмов, которые пользователь уже видел."""
        rows = self._conn.execute(
            "SELECT kinopoisk_id FROM user_shown_movies WHERE vk_id = ?",
            (vk_id,),
        ).fetchall()
        return {r["kinopoisk_id"] for r in rows}

    def mark_movies_shown(self, vk_id: int, kinopoisk_ids: List[int]) -> None:
        """Отмечает фильмы показанными. Повторный вызов безопасен."""
        with self._conn:
            self._conn.executemany(
                "INSERT OR IGNORE INTO user_shown_movies (vk_id, kinopoisk_id) VALUES (?, ?)",
                [(vk_id, i) for i in kinopoisk_ids],
            )

    # ------------------------------------------------------------------
    # Список ожидания
    # ------------------------------------------------------------------

    def add_to_waiting_list(self, vk_id: int, movie: Movie) -> None:
        """Добавляет фильм в «посмотрю позже» (и кэширует сам фильм)."""
        with self._conn:
            self._upsert_movie(movie)
            self._conn.execute(
                "INSERT OR IGNORE INTO user_waiting_list (vk_id, kinopoisk_id) VALUES (?, ?)",
                (vk_id, movie.kinopoisk_id),
            )

    def get_waiting_list(self, vk_id: int) -> List[Movie]:
        """Все отложенные фильмы пользователя (JOIN склеивает ID с данными)."""
        rows = self._conn.execute(
            """
            SELECT m.*
            FROM user_waiting_list w
            JOIN movies m ON m.kinopoisk_id = w.kinopoisk_id
            WHERE w.vk_id = ?
            ORDER BY w.added_at
            """,
            (vk_id,),
        ).fetchall()
        return [self._row_to_movie(r) for r in rows]

    def remove_from_waiting_list(self, vk_id: int, kinopoisk_id: int) -> None:
        with self._conn:
            self._conn.execute(
                "DELETE FROM user_waiting_list WHERE vk_id = ? AND kinopoisk_id = ?",
                (vk_id, kinopoisk_id),
            )


# --- Самопроверка репозитория ---
if __name__ == "__main__":
    import os
    from core.database import Database

    TEST_DB = "test_movie_repo.sqlite"
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    # Порядок важен: сначала ядро (users), потом репозиторий
    db = Database(TEST_DB)
    repo = MovieRepository(db.connection)

    db.ensure_user(1)
    repo.set_user_genres(1, ["фантастика", "драма"])
    print("Жанры:", repo.get_user_genres(1))

    movie = Movie(kinopoisk_id=100, title="Интерстеллар",
                  rating=8.6, votes=500000, genres=["фантастика", "драма"])
    repo.add_to_waiting_list(1, movie)
    print("Ожидание:", [m.title for m in repo.get_waiting_list(1)])

    repo.mark_movies_shown(1, [100])
    print("Показано:", repo.get_shown_ids(1))

    db.close()
    os.remove(TEST_DB)
    print("✓ Проверки MovieRepository прошли")