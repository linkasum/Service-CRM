#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from sqlmodel import Session, select
from core.database import engine
from models.document_template_assignment import DocumentTemplateAssignment

with Session(engine) as session:
    # Удаляем все назначения для receipt
    old = session.exec(
        select(DocumentTemplateAssignment)
        .where(DocumentTemplateAssignment.document_type == 'receipt')
    ).all()
    
    for o in old:
        session.delete(o)
        print(f"Удалено назначение ID={o.id}")
    
    session.commit()
    print("Готово!")
