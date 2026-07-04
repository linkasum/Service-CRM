"""
Модель: Пользователь (сотрудник)
"""
from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import BigInteger, Column


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=100, description="Логин для входа")
    full_name: Optional[str] = Field(default=None, max_length=200, description="Полное имя (отображаемое)")
    password_hash: str = Field(max_length=255)
    role_id: Optional[int] = Field(default=None, foreign_key="roles.id")
    salary_config_id: Optional[int] = Field(default=None, foreign_key="salary_configs.id", description="Формула зарплаты")
    email: Optional[str] = Field(default=None, max_length=200)
    phone: Optional[str] = Field(default=None, max_length=20)
    telegram_chat_id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, unique=True, index=True),
    )
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)

    # Связи
    role: Optional["Role"] = Relationship(back_populates="users")
    orders_as_master: List["Order"] = Relationship(
        back_populates="master",
        sa_relationship_kwargs={"foreign_keys": "Order.master_id"}
    )
    orders_as_acceptor: List["Order"] = Relationship(
        back_populates="acceptor",
        sa_relationship_kwargs={"foreign_keys": "Order.acceptor_id"}
    )
    salary_records: List["SalaryRecord"] = Relationship(back_populates="user")

    def __repr__(self):
        return f"<User {self.username}>"
