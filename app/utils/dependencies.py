"""
Общие зависимости для эндпоинтов (DI).
Импорт get_db здесь — единая точка для FastAPI Depends().
"""

from app.core.database import get_db

__all__ = ["get_db"]
