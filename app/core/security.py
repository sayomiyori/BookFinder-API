"""
Безопасность: хеширование паролей (bcrypt) и JWT.
Используем bcrypt напрямую, чтобы избежать ошибки passlib на платформах с длинным тестовым паролем.
"""

import bcrypt
from datetime import datetime, timezone, timedelta
from typing import Any

from jose import JWTError, jwt

from app.core.config import get_settings

# Bcrypt принимает не более 72 байт
BCRYPT_MAX_PASSWORD_BYTES = 72


def _password_bytes(password: str) -> bytes:
    """Пароль в байтах, обрезанный до лимита bcrypt."""
    raw = password.encode("utf-8")
    return raw[:BCRYPT_MAX_PASSWORD_BYTES] if len(raw) > BCRYPT_MAX_PASSWORD_BYTES else raw


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля против хеша."""
    return bcrypt.checkpw(
        _password_bytes(plain_password),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """Хеширование пароля для хранения в БД."""
    return bcrypt.hashpw(
        _password_bytes(password),
        bcrypt.gensalt(),
    ).decode("utf-8")


def create_access_token(subject: str | int, expires_delta: timedelta | None = None) -> str:
    """
    Создание JWT access token.
    subject — идентификатор пользователя (обычно email или id).
    """
    settings = get_settings()
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode: dict[str, Any] = {"sub": str(subject), "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> str | None:
    """
    Декодирование JWT и извлечение subject (sub).
    Возвращает None при невалидном или истёкшем токене.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload.get("sub")
    except JWTError:
        return None
