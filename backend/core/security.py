"""
Безопасность: JWT и хеширование паролей
"""
from datetime import datetime, timedelta
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select

from core.config import get_settings
from core.database import get_session

settings = get_settings()
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверить пароль"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """Хешировать пароль"""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создать JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Создать JWT refresh token (долгий срок жизни)"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Расшифровать JWT токен"""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен авторизации",
            headers={"WWW-Authenticate": "Bearer"},
        )


def decode_token(token: str) -> Optional[dict]:
    """Расшифровать JWT токен без выброса исключения (для WebSocket)"""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), session: Session = Depends(get_session)):
    """Получить текущего пользователя из токена"""
    token_data = decode_access_token(credentials.credentials)

    from models.user import User

    user = session.exec(select(User).where(User.username == token_data.get("sub"))).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден или неактивен",
        )
    return user


def require_permission(permission: str):
    """
    Проверка наличия конкретного права доступа.
    Учитывает role.permissions (JSON) + individual_permissions (таблица).
    """
    def check_permission(current_user=Depends(get_current_user), session: Session = Depends(get_session)):
        if not current_user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав: требуется {permission}",
            )
        from models.individual_permission import IndividualPermission
        from sqlmodel import select as _select

        perms = set(current_user.role.permissions)
        ind_rows = session.exec(
            _select(IndividualPermission).where(
                IndividualPermission.user_id == current_user.id
            )
        ).all()
        for ip in ind_rows:
            if ip.permission.startswith("-"):
                perms.discard(ip.permission[1:])
            else:
                perms.add(ip.permission)
        if permission not in perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав: требуется {permission}",
            )
        return current_user
    return check_permission
