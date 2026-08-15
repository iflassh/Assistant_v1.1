# core/database.py
# ФУНДАМЕНТ базы данных: подключение + общие таблицы.
#
# Ответственность после рефакторинга:
#   1. Открыть ОДНО подключение SQLite на всё приложение.
#   2. Создать общие таблицы (users).
#   3. Отдать подключение модулям через Dependency Injection.
#
# Ядро больше НЕ знает про фильмы, афишу и новости.
# Таблицы модулей живут в их репозиториях
# (например, modules/movies/repository.py).

import sqlite3
from typing import Optional

from core.models import User


class Database:
    """Фундамент БД: подключение и общие для всех модулей таблицы."""

    def __init__(self, db_path: str):
        # Одно подключение на всё приложение.
        # check_same_thread=False — чтобы в будущем VK-бот и планировщик
        # (APScheduler) могли обращаться к БД из своих потоков.
        self._conn = sqlite3.connect(db_path, check_same_thread=False)

        # Доступ к колонкам по имени: row["vk_id"] вместо row[0].
        self._conn.row_factory = sqlite3.Row

        self._init_shared_schema()

    # ------------------------------------------------------------------
    # Служебное
    # ------------------------------------------------------------------

    @property
    def connection(self) -> sqlite3.Connection:
        """
        Отдаёт подключение наружу (Dependency Injection).

        Модули не открывают свои подключения — они получают это
        и работают через свои репозитории.
        """
        return self._conn

    def _init_shared_schema(self) -> None:
        """Создаёт общие таблицы. Безопасно вызывать повторно."""
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                vk_id INTEGER PRIMARY KEY
            );
            """
        )

    def close(self) -> None:
        """Закрывает подключение. Вызывается при остановке бота."""
        self._conn.close()

    # ------------------------------------------------------------------
    # Общие данные: пользователи
    # ------------------------------------------------------------------

    def ensure_user(self, vk_id: int) -> None:
        """Создаёт пользователя, если его нет. Если есть — ничего не делает."""
        with self._conn:
            self._conn.execute(
                "INSERT OR IGNORE INTO users (vk_id) VALUES (?)", (vk_id,)
            )

    def user_exists(self, vk_id: int) -> bool:
        """Проверяет, зарегистрирован ли пользователь в ассистенте."""
        row = self._conn.execute(
            "SELECT 1 FROM users WHERE vk_id = ?", (vk_id,)
        ).fetchone()
        return row is not None

    def get_user(self, vk_id: int) -> Optional[User]:
        """
        Возвращает User БЕЗ модульных предпочтений (или None).

        ВАЖНО: ядро не знает про жанры — это собственность модуля фильмов.
        Модуль сам «обогащает» пользователя своими данными
        (см. MovieRepository.get_user_genres).
        """
        if not self.user_exists(vk_id):
            return None
        return User(vk_id=vk_id)


# --- Самопроверка ядра ---
if __name__ == "__main__":
    import os

    TEST_DB = "test_core_db.sqlite"
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

    db = Database(TEST_DB)
    db.ensure_user(1)
    print("Пользователь существует:", db.user_exists(1))
    print("Пользователь:", db.get_user(1))
    print("Несуществующий:", db.get_user(999))

    db.close()
    os.remove(TEST_DB)
    print("✓ Проверки ядра Database прошли")