# modules/movies/client.py
# Клиент для работы с API фильмов (poiskkino.dev).
# Отвечает только за общение с API и проверку его доступности.

import requests
from dataclasses import dataclass
from typing import List, Optional

from modules.movies.models import Movie
from modules.movies.config import MovieSettings


@dataclass
class ApiHealthResult:
    """Результат проверки здоровья API."""
    is_ok: bool
    message: str
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None


class MovieApiClient:
    """
    Клиент для API фильмов.

    Инкапсулирует всю логику общения с внешним API.
    Другие части программы не знают, как именно устроен API —
    они просто вызывают методы этого класса.
    """

    def __init__(self, settings: MovieSettings):
        self._base_url = settings.base_url.rstrip("/")  # Убираем слэш в конце
        self._api_key = settings.api_key
        self._timeout = 10  # секунд на запрос

    def _build_headers(self) -> dict:
        """Собирает заголовки запроса."""
        headers = {
            "Accept": "application/json",
        }
        # Если API-ключ задан, добавляем его в заголовки.
        # Точный формат авторизации зависит от API.
        # Возможные варианты: Bearer token, X-API-Key, query parameter.
        if self._api_key:
            headers["X-API-Key"] = self._api_key
            # Альтернатива: headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def health_check(self) -> ApiHealthResult:
        """
        Проверяет, доступен ли API и отвечает ли он корректно.

        Возвращает ApiHealthResult с понятным сообщением.
        """
        url = f"{self._base_url}/movie"

        try:
            # Делаем тестовый запрос с минимальными параметрами
            response = requests.get(
                url,
                headers=self._build_headers(),
                params={"limit": 1},  # Просим один фильм для проверки
                timeout=self._timeout,
            )

            response_time = response.elapsed.total_seconds() * 1000

            # --- Проверяем HTTP-статус ---
            if response.status_code == 401:
                return ApiHealthResult(
                    is_ok=False,
                    message="API-ключ недействителен или отсутствует (401 Unauthorized)",
                    status_code=401,
                    response_time_ms=response_time,
                )

            if response.status_code == 403:
                return ApiHealthResult(
                    is_ok=False,
                    message="Доступ запрещён. Проверьте права API-ключа (403 Forbidden)",
                    status_code=403,
                    response_time_ms=response_time,
                )

            if response.status_code == 404:
                return ApiHealthResult(
                    is_ok=False,
                    message=f"Неверный URL: {url} (404 Not Found). Проверьте base_url.",
                    status_code=404,
                    response_time_ms=response_time,
                )

            if response.status_code == 429:
                return ApiHealthResult(
                    is_ok=False,
                    message="Превышен лимит запросов к API (429 Too Many Requests)",
                    status_code=429,
                    response_time_ms=response_time,
                )

            if response.status_code >= 500:
                return ApiHealthResult(
                    is_ok=False,
                    message=f"Ошибка на стороне сервера API ({response.status_code})",
                    status_code=response.status_code,
                    response_time_ms=response_time,
                )

            # --- Проверяем, что ответ — валидный JSON ---
            try:
                data = response.json()
            except ValueError:
                return ApiHealthResult(
                    is_ok=False,
                    message=f"API вернул не JSON. Статус: {response.status_code}. Тело: {response.text[:200]}",
                    status_code=response.status_code,
                    response_time_ms=response_time,
                )

            # --- Проверяем структуру ответа ---
            # Здесь мы проверяем, что в ответе есть то, что мы ожидаем.
            # Точная структура зависит от API — уточним по документации.
            # Пример: ожидаем поле "docs" или "data" со списком фильмов.
            if not isinstance(data, (dict, list)):
                return ApiHealthResult(
                    is_ok=False,
                    message="API вернул неожиданный формат данных (не dict и не list)",
                    status_code=response.status_code,
                    response_time_ms=response_time,
                )

            # Если дошли сюда — всё хорошо
            return ApiHealthResult(
                is_ok=True,
                message=f"API доступен. Время ответа: {response_time:.0f}ms",
                status_code=response.status_code,
                response_time_ms=response_time,
            )

        except requests.exceptions.Timeout:
            return ApiHealthResult(
                is_ok=False,
                message=f"API не отвечает в течение {self._timeout} секунд (таймаут)",
            )

        except requests.exceptions.ConnectionError:
            return ApiHealthResult(
                is_ok=False,
                message="Не удалось подключиться к API. Проверьте интернет и base_url.",
            )

        except requests.exceptions.RequestException as e:
            return ApiHealthResult(
                is_ok=False,
                message=f"Неизвестная ошибка при запросе к API: {e}",
            )

    def fetch_movies(self, limit: int = 50) -> List[Movie]:
        """
        Получает список фильмов из API.

        Здесь будет реальная логика получения фильмов.
        Пока оставим заглушку, которую реализуем на следующем этапе.
        """
        # TODO: Реализовать на следующем этапе
        raise NotImplementedError("Метод fetch_movies будет реализован позже")