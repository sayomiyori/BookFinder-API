"""
Singleton slowapi Limiter для rate limiting.
Вынесен в отдельный модуль, чтобы избежать циклических импортов
между app.main и роутерами.

RATE_LIMIT_ENABLED=false отключает лимиты (используется в тестах/CI).
"""

import os

from slowapi import Limiter
from slowapi.util import get_remote_address

_enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() not in ("false", "0", "no")

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],
    enabled=_enabled,
)
