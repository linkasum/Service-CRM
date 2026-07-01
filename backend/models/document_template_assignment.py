"""
Модель назначений шаблонов на типы документов
"""
from sqlmodel import SQLModel, Field, UniqueConstraint
from typing import Optional
from datetime import datetime


class DocumentTemplateAssignment(SQLModel, table=True):
    """Назначение шаблона на тип документа"""
    __tablename__ = "document_template_assignments"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    document_type: str = Field(..., max_length=50, description="Тип документа (receipt, diagnostic_act, etc.)")
    template_id: int = Field(..., foreign_key="document_templates.id", description="ID шаблона")
    is_active: bool = Field(default=True, description="Активное назначение")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint("document_type", "is_active", name="uq_document_type_active"),
    )
