"""
Singleton slowapi Limiter для rate limiting.
Вынесен в отдельный модуль, чтобы избежать циклических импортов
между app.main и роутерами.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
