"""Pydantic-схемы для пользователя."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# Bcrypt принимает не более 72 байт — ограничиваем длину пароля
PASSWORD_MAX_LENGTH = 72


class UserCreate(BaseModel):
    """Тело запроса регистрации."""

    email: EmailStr = Field(..., description="Email пользователя")
    password: str = Field(
        ...,
        min_length=6,
        max_length=PASSWORD_MAX_LENGTH,
        description="Пароль (6–72 символа)",
    )


class UserLogin(BaseModel):
    """Тело запроса входа."""

    email: EmailStr = Field(..., description="Email пользователя")
    password: str = Field(..., max_length=PASSWORD_MAX_LENGTH, description="Пароль")


class UserResponse(BaseModel):
    """Публичные данные пользователя в ответе."""

    id: int
    email: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
