# core/models.py
# Общие модели, которые нужны ВСЕМ модулям ассистента.

from dataclasses import dataclass, field
from typing import List


@dataclass
class User:
    """
    Пользователь ассистента.

    Это общая модель — она нужна и модулю фильмов,
    и будущему модулю новостей, и модулю событий.
    """
    vk_id: int
    preferred_genres: List[str] = field(default_factory=list)

    # В будущем сюда можно добавить:
    # preferred_topics: List[str]  — для новостей
    # city: str                    — для событий в городе
    # subscribed_modules: List[str] — какие модули активны для пользователя