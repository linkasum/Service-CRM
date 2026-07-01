"""
Auth маршруты: логин, JWT, привязка Telegram
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime

from core.database import get_session
from core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)
from models.user import User
from models.role import Role
from models.salary_config import SalaryConfig
from schemas.user import UserLogin, Token, UserRead, UserReadWithRole, ChangePassword, RefreshToken
from core.logging import logger

router = APIRouter(prefix="/api/auth", tags=["Аутентификация"])


def build_user_read_with_role(user: User, session: Session) -> UserReadWithRole:
    role = None
    role_name = None
    permissions = []
    if user.role_id:
        role = session.get(Role, user.role_id)
        if role:
            role_name = role.name
            permissions = role.permissions

    salary_cfg = session.get(SalaryConfig, user.salary_config_id) if user.salary_config_id else None

    user_dict = user.model_dump()
    user_dict["role_name"] = role_name
    user_dict["permissions"] = permissions
    user_dict["email"] = getattr(user, "email", None)
    user_dict["phone"] = getattr(user, "phone", None)
    user_dict["salary_config_name"] = salary_cfg.name if salary_cfg else None
    user_dict["salary_formula"] = salary_cfg.formula_string if salary_cfg else None
    user_dict["salary_config_type"] = salary_cfg.config_type.value if salary_cfg and salary_cfg.config_type else None
    user_dict["salary_fixed_amount"] = salary_cfg.fixed_amount if salary_cfg else None
    user_dict["salary_period"] = salary_cfg.period.value if salary_cfg and salary_cfg.period else None
    return UserReadWithRole(**user_dict)


@router.post("/login", response_model=Token, summary="Вход в систему")
def login(credentials: UserLogin, session: Session = Depends(get_session)):
    """Аутентификация пользователя и получение JWT токена"""
    user = session.exec(select(User).where(User.username == credentials.username)).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Учётная запись отключена",
        )
    
    access_token = create_access_token(data={"sub": user.username, "role_id": user.role_id})
    refresh_token = create_refresh_token(data={"sub": user.username, "role_id": user.role_id})
    user_data = build_user_read_with_role(user, session)

    logger.info(f"Пользователь {user.username} вошёл в систему")
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_data,
    )


@router.get("/me", response_model=UserReadWithRole, summary="Текущий пользователь")
def get_me(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    """Получить информацию о текущем пользователе"""
    return build_user_read_with_role(current_user, session)


@router.post("/refresh", summary="Обновить access token")
def refresh_token(
    data: RefreshToken,
    session: Session = Depends(get_session),
):
    """
    Обновить access token используя refresh token.
    """
    payload = decode_token(data.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный refresh token",
        )

    # Проверяем что это refresh token
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный тип токена",
        )

    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный refresh token",
        )

    # Проверяем что пользователь активен
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден или неактивен",
        )

    # Создаём новый access token
    new_access_token = create_access_token(data={"sub": user.username, "role_id": user.role_id})

    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/telegram/link", summary="Привязка Telegram аккаунта")
def link_telegram(
    telegram_code: str,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Привязка Telegram аккаунта к пользователю.
    telegram_code — код из админ-панели, который вводится в боте.
    """
    # Здесь должна быть логика проверки кода через бота
    # Пока — заглушка
    logger.info(f"Запрос на привязку Telegram от пользователя {current_user.username}, код: {telegram_code}")
    
    return {"message": "Код принят. Введите его в Telegram боте для завершения привязки."}


@router.post("/telegram/confirm", summary="Подтверждение Telegram из бота")
def confirm_telegram(
    chat_id: int,
    code: str,
    session: Session = Depends(get_session),
):
    """
    Подтверждение привязки Telegram из бота.
    Вызывается ботом когда пользователь вводит код.
    """
    # Ищем пользователя по коду (код хранится во временном хранилище или Redis)
    # Пока — заглушка
    logger.info(f"Подтверждение Telegram: chat_id={chat_id}, code={code}")
    
    return {"message": "Telegram аккаунт привязан"}


@router.post("/change-password", summary="Смена пароля")
def change_password(
    pwd_data: ChangePassword,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Сменить пароль текущего пользователя"""
    if not verify_password(pwd_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный текущий пароль",
        )

    current_user.password_hash = get_password_hash(pwd_data.new_password)
    session.add(current_user)
    session.commit()

    logger.info(f"Пользователь {current_user.username} сменил пароль")
    return {"message": "Пароль успешно изменён"}
