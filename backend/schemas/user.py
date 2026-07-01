"""
Схемы для User
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str
    role_id: Optional[int] = None
    telegram_chat_id: Optional[int] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    role_id: Optional[int] = None
    telegram_chat_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserRead(UserBase):
    id: int
    role_id: Optional[int] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    salary_config_id: Optional[int] = None
    salary_config_name: Optional[str] = None
    salary_formula: Optional[str] = None
    salary_config_type: Optional[str] = None
    salary_fixed_amount: Optional[float] = None
    salary_period: Optional[str] = None
    telegram_chat_id: Optional[int] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserReadWithRole(UserRead):
    role_name: Optional[str] = None
    permissions: list = []


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: UserReadWithRole


class RefreshToken(BaseModel):
    refresh_token: str


class ChangePassword(BaseModel):
    current_password: str
    new_password: str
