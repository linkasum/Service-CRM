"""
Модель: Шаблон документа
"""
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text


class DocumentTemplate(SQLModel, table=True):
    __tablename__ = "document_templates"

    id: Optional[int] = Field(default=None, primary_key=True)
    type: str = Field(
        max_length=50,
        unique=True,
        index=True,
        description="Тип: receipt, diagnostic_act, work_act, invoice"
    )
    content_template: str = Field(
        sa_column=Column(Text),
        description="HTML или текст для PDF"
    )
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def __repr__(self):
        return f"<DocumentTemplate {self.type}>"
