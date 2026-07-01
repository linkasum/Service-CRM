"""
Схемы для Role
"""
from typing import Optional, List
from pydantic import BaseModel


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[str] = []


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


class RoleRead(RoleBase):
    id: int

    class Config:
        from_attributes = True
