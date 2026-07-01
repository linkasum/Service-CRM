#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from sqlmodel import Session, select
from core.database import engine
from models.document_template import DocumentTemplate
from models.document_template_assignment import DocumentTemplateAssignment

with Session(engine) as session:
    print("=== ШАБЛОНЫ ===")
    templates = session.exec(select(DocumentTemplate)).all()
    for t in templates:
        content_preview = t.content_template[:50] if t.content_template else "ПУСТОЙ"
        print(f"ID={t.id} type={t.type}: {content_preview}...")
    
    print("\n=== НАЗНАЧЕНИЯ ===")
    assignments = session.exec(select(DocumentTemplateAssignment).where(DocumentTemplateAssignment.is_active == True)).all()
    for a in assignments:
        template = session.get(DocumentTemplate, a.template_id)
        content_ok = "✓" if template and template.content_template else "✗ ПУСТОЙ"
        print(f"{a.document_type} → template_id={a.template_id} {content_ok}")
