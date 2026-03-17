"""
Эндпоинты аутентификации: регистрация, логин, текущий пользователь.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.limiter import limiter
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.utils.dependencies import get_current_user, get_db

router = APIRouter()


@router.post(
    "/register",
    response_model=Token,
    summary="Регистрация нового пользователя",
    responses={
        201: {"description": "Пользователь создан, возвращает JWT"},
        400: {"description": "Email уже зарегистрирован"},
    },
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Регистрация нового пользователя.
    **Rate limit:** 5 запросов в минуту с одного IP.
    Возвращает JWT access token.
    """
    result = await db.execute(select(User).where(User.email == data.email))
    existing = result.scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже зарегистрирован",
        )
    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        is_active=True,
    )
    db.add(user)
    await db.flush()
    token = create_access_token(subject=user.email)
    return Token(access_token=token, token_type="bearer")


async def _login_with_credentials(email: str, password: str, db: AsyncSession) -> Token:
    """Общая логика входа по email и паролю."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт деактивирован",
        )
    return Token(access_token=create_access_token(subject=user.email), token_type="bearer")


@router.post(
    "/login",
    response_model=Token,
    summary="Вход по JSON",
    responses={
        200: {"description": "Успешный вход, возвращает JWT"},
        401: {"description": "Неверные учётные данные"},
        403: {"description": "Аккаунт деактивирован"},
    },
)
@limiter.limit("10/minute")
async def login(
    request: Request,
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Вход по email и паролю (JSON body).
    **Rate limit:** 10 запросов в минуту с одного IP.
    """
    return await _login_with_credentials(data.email, data.password, db)


@router.post(
    "/login/form",
    response_model=Token,
    include_in_schema=True,
    summary="Вход через Swagger UI (form)",
)
@limiter.limit("10/minute")
async def login_form(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Вход через form (для кнопки **Authorize** в Swagger UI).
    `username` = email, `password` = пароль.
    """
    return await _login_with_credentials(form_data.username, form_data.password, db)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Текущий пользователь",
    responses={
        200: {"description": "Данные авторизованного пользователя"},
        401: {"description": "Токен отсутствует или истёк"},
    },
)
async def me(current_user: User = Depends(get_current_user)) -> User:
    """Информация о текущем авторизованном пользователе."""
    return current_user
