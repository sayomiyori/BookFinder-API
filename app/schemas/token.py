"""Pydantic-схемы для JWT токена."""

from pydantic import BaseModel, Field


class Token(BaseModel):
    """Ответ с access token после логина/регистрации."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Тип токена")


class TokenPayload(BaseModel):
    """Полезная нагрузка JWT (для документации)."""

    sub: str = Field(..., description="Идентификатор пользователя (email)")
    exp: int = Field(..., description="Время истечения (Unix timestamp)")
