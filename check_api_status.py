# check_api.py
# Скрипт для быстрой проверки доступности API.
# Запускайте его, если что-то пошло не так.

from modules.movies.config import load_movie_settings
from modules.movies.client import MovieApiClient


def main():
    print("=" * 50)
    print("Проверка API фильмов")
    print("=" * 50)

    # Загружаем настройки модуля фильмов
    settings = load_movie_settings()
    print(f"Base URL: {settings.base_url}")
    print(f"API ключ: {'задан' if settings.api_key else 'не задан'}")
    print("-" * 50)

    # Создаём клиент и проверяем
    client = MovieApiClient(settings)
    result = client.health_check()

    if result.is_ok:
        print(f"✅ {result.message}")
        if result.status_code:
            print(f"   HTTP статус: {result.status_code}")
        if result.response_time_ms:
            print(f"   Время ответа: {result.response_time_ms:.0f}ms")
    else:
        print(f"❌ {result.message}")
        if result.status_code:
            print(f"   HTTP статус: {result.status_code}")
        print("\nВозможные решения:")
        print("  1. Проверьте интернет-соединение")
        print("  2. Проверьте правильность base_url в .env")
        print("  3. Проверьте актуальность API-ключа")
        print("  4. Попробуйте позже (возможно, API временно недоступен)")

    print("=" * 50)


if __name__ == "__main__":
    main()