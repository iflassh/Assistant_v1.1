# config.py
# Глобальные настройки всего ассистента.
# Не путать с настройками конкретных модулей (например, modules/movies/config.py).

import os
import sys
from dataclasses import dataclass
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

@dataclass(frozen=True)
class AppSettings:
    """Общие настройки бота."""
    vk_token: str
    db_path: str
    debug: bool

def load_app_settings() -> AppSettings:
    """Читает глобальные настройки и проверяет их (Fail Fast)."""
    vk_token = os.getenv("VK_BOT_TOKEN", "").strip()
    db_path = os.getenv("DB_PATH", "bot_database.sqlite").strip()
    debug = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

    # --- Fail Fast: проверка критически важных секретов ---
    if not vk_token:
        print("❌ ОШИБКА КОНФИГУРАЦИИ: Переменная VK_BOT_TOKEN не найдена или пуста!")
        print("   Проверь файл .env и убедись, что ты указал токен группы ВКонтакте.")
        sys.exit(1)  # Завершаем работу программы с кодом ошибки

    return AppSettings(
        vk_token=vk_token,
        db_path=db_path,
        debug=debug,
    )

if __name__ == "__main__":
    print("--- Тестируем глобальные настройки ---")
    settings = load_app_settings()
    print("✓ Глобальные настройки загружены!")
    print(f"  Токен VK: {'*' * 10}{settings.vk_token[-4:]}") # Показываем только последние 4 символа
    print(f"  Путь к БД: {settings.db_path}")
    print(f"  Режим отладки: {settings.debug}")