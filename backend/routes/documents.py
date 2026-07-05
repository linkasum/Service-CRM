"""
Documents маршруты: генерация PDF документов, управление документами
"""
import os
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlmodel import Session, select, func

from core.database import get_session
from core.security import get_current_user
from models.order import Order
from models.user import User
from models.document import Document
from services.document_service import DocumentService
from core.logging import logger

router = APIRouter(prefix="/api/documents", tags=["Документы"])

# Абсолютный путь к директории документов (проект корень, не backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOCUMENTS_DIR = os.path.join(BASE_DIR, "documents")


@router.get("/print/{order_id}/{template_type}", summary="Печать документа (HTML для браузера)")
def print_document_html(
    order_id: int,
    template_type: str,
    token: Optional[str] = Query(None, description="JWT токен для авторизации"),
    session: Session = Depends(get_session),
):
    """
    Вернуть HTML для печати документа в браузере.
    Аналог HelloClient - браузер рендерит PDF через печать.
    Авторизация через query parameter ?token=xxx
    """
    from models.document_template import DocumentTemplate
    from models.document_template_assignment import DocumentTemplateAssignment
    from models.company_settings import CompanySettings
    from core.security import decode_token
    
    # Авторизация через токен в query parameter
    if not token:
        raise HTTPException(status_code=401, detail="Требуется токен авторизации")
    
    try:
        payload = decode_token(token)
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Неверный токен")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Ошибка авторизации: {str(e)}")
    
    current_user = session.exec(select(User).where(User.username == username)).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    # Найти шаблон (сначала назначение, потом по типу)
    assignment = session.exec(
        select(DocumentTemplateAssignment)
        .where(DocumentTemplateAssignment.document_type == template_type)
        .where(DocumentTemplateAssignment.is_active == True)
    ).first()

    template = None
    if assignment:
        template = session.get(DocumentTemplate, assignment.template_id)
    
    if not template:
        template = session.exec(
            select(DocumentTemplate).where(DocumentTemplate.type == template_type)
        ).first()
    
    if not template or not template.content_template:
        raise HTTPException(status_code=404, detail=f"Шаблон '{template_type}' не найден")
    
    # Получить данные компании
    company = session.exec(select(CompanySettings)).first()
    
    # Подготовить контекст переменных
    ctx = {
        "order_id": str(order.id),
        "client_name": order.client_name or "",
        "client_phone": order.client_phone or "",
        "client_email": order.client_email or "",
        "device_model": order.device_model or "",
        "device_brand": order.device_brand or "",
        "device_category": order.device_category or "",
        "serial_number": order.serial_number or "",
        "accessories": order.accessories or "",
        "appearance": order.appearance or "не указан",
        "complaint": order.complaint or "",
        "diagnostics": order.diagnostic_act_text or "Не указаны",
        "total_cost": f"{order.total_cost or 0:.2f}",
        "parts_cost": f"{order.parts_cost or 0:.2f}",
        "work_cost": f"{order.work_cost or 0:.2f}",
        "created_at": order.created_at.strftime("%d.%m.%Y %H:%M") if order.created_at else "",
        "order_date": order.created_at.strftime("%d.%m.%Y") if order.created_at else "",
        "order_status": order.status or "",
        "issued_at": order.issued_at.strftime("%d.%m.%Y %H:%M") if order.issued_at else "—",
        "warranty_days": str(order.warranty_days or 30),
        "diagnostic_act_text": order.diagnostic_act_text or "Не указаны",
        "now": datetime.now().strftime("%d.%m.%Y"),
        "print_time": datetime.now().strftime("%H:%M"),
        "status": order.status or "",
        "master_name": order.master.username if order.master else (order.manager_name or "—"),
        "acceptor_name": order.acceptor.username if order.acceptor else "—",
    }
    
    # Добавить данные компании
    if company:
        ctx.update({
            "company_name": company.company_name or "",
            "company_inn": company.inn or "",
            "company_address": company.address or "",
            "company_phone": company.phone or "",
            "company_email": company.email or "",
        })

    # QR-код для оплаты счета
    if template_type == "invoice":
        try:
            import qrcode, io, base64
            from qrcode.image.styledpil import StyledPilImage
            from qrcode.image.styles.moduledrawers import SquareModuleDrawer

            total = order.total_cost or 0
            total_kop = int(total * 100)
            purpose = f"Оплата по счету {order_id}"
            if order.device_model:
                purpose += f" за ремонт {order.device_model}"
            if len(purpose) > 210:
                purpose = purpose[:210]

            inn = getattr(company, 'inn', '') if company else ''
            account = getattr(company, 'account', '') if company else ''
            bik = getattr(company, 'bik', '') if company else ''
            bank = getattr(company, 'bank', '') if company else ''

            parts = ["ST00012"]
            if company: parts.append(f"Name={company.company_name or ''}")
            if account: parts.append(f"PersonalAcc={account}")
            if bank: parts.append(f"BankName={bank}")
            if bik: parts.append(f"BIC={bik}")
            if inn: parts.append(f"PayeeINN={inn}")
            parts.append(f"Purpose={purpose}")
            parts.append(f"Sum={total_kop}")
            qr_data = "|".join(parts)

            qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=4, border=2)
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(image_factory=StyledPilImage, module_drawer=SquareModuleDrawer(), fill_color="black", back_color="white")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            qr_b64 = base64.b64encode(buf.getvalue()).decode()
            ctx["qr_code_data"] = f"data:image/png;base64,{qr_b64}"
        except Exception:
            ctx["qr_code_data"] = ""

    # Генерируем таблицу услуг и запчастей динамически
    items_rows = []
    idx = 0
    
    # Для work_act — одна строка с общей суммой
    if template_type == "work_act":
        service_names = ", ".join(si.service_name for si in order.service_items) if order.service_items else (order.complaint or "Ремонт")
        total = order.total_cost or 0
        items_rows.append(
            f'<tr><td>1</td>'
            f'<td>{service_names}</td>'
            f'<td style="text-align:right">{order.warranty_days or 30}</td>'
            f'<td style="text-align:right">{total:.2f}</td>'
            f'<td style="text-align:right">0.00</td>'
            f'<td style="text-align:right">1</td>'
            f'<td style="text-align:right">{total:.2f}</td></tr>'
        )
    else:
        # Услуги
        if order.service_items:
            for si in order.service_items:
                idx += 1
                price = si.price_at_order or 0
                qty = si.quantity or 1
                row_total = price * qty
                items_rows.append(
                    f'<tr><td>{idx}</td>'
                    f'<td>{si.service_name or "Услуга"}</td>'
                    f'<td style="text-align:right">{order.warranty_days or 30}</td>'
                    f'<td style="text-align:right">{price:.2f}</td>'
                    f'<td style="text-align:right">0.00</td>'
                    f'<td style="text-align:right">{qty}</td>'
                    f'<td style="text-align:right">{row_total:.2f}</td></tr>'
                )
        
        # Запчасти
        if order.parts:
            for op in order.parts:
                idx += 1
                price = op.price_at_order or 0
                qty = op.quantity or 1
                row_total = price * qty
                part_name = op.part.name if op.part else "Запчасть"
                items_rows.append(
                    f'<tr><td>{idx}</td>'
                    f'<td>{part_name}</td>'
                    f'<td style="text-align:right">{order.warranty_days or 30}</td>'
                    f'<td style="text-align:right">{price:.2f}</td>'
                    f'<td style="text-align:right">0.00</td>'
                    f'<td style="text-align:right">{qty}</td>'
                    f'<td style="text-align:right">{row_total:.2f}</td></tr>'
                )
    
    ctx["items_table"] = "\n".join(items_rows) if items_rows else ""

    # Подставить переменные в шаблон
    html_content = template.content_template
    
    # Авто-фикс: чиним шаблон если редактор сломал структуру
    # 1. Если {items_table} вне таблицы — ищем <tbody> внутри таблицы и вставляем туда
    import re as _re
    if '{items_table}' in html_content and '<tr>' not in html_content:
        # Ищем последний <tbody> внутри <table>
        m = _re.search(r'(<table[^>]*>\s*<thead>.*?</thead>\s*<tbody>\s*)(\s*</tbody>\s*</table>)', html_content, _re.DOTALL)
        if m:
            html_content = html_content.replace('{items_table}', '')
            html_content = html_content[:m.start(2)] + '{items_table}' + html_content[m.start(2):]
    
    for key, value in ctx.items():
        html_content = html_content.replace(f"{{{key}}}", str(value))
    
    # 2. После подстановки: убираем <p> вокруг <tr> (WYSIWYG так делает)
    if '<tr>' in ctx.get("items_table", ""):
        html_content = _re.sub(r'<p>\s*(<tr>)', r'\1', html_content)
        html_content = _re.sub(r'(</tr>)\s*</p>', r'\1', html_content)
    
    # Извлечь <style> блоки из шаблона и перенести в <head>
    if '<tr>' in ctx.get("items_table", ""):
        # Убираем <p> вокруг строк таблицы
        html_content = _re.sub(r'<p>\s*(<tr>.*?</tr>)\s*</p>', r'\1', html_content, flags=_re.DOTALL)
        html_content = _re.sub(r'<p>\s*(<tr>.*?</tr>)\s*</p>', r'\1', html_content, flags=_re.DOTALL)
        # Если items_table оказался ПОСЛЕ </table>, переносим его в последний <tbody> перед </table>
        html_content = _re.sub(
            r'(<table[^>]*>\s*<thead>.*?</thead>\s*<tbody>\s*)\s*</tbody>\s*</table>\s*(<tr>)',
            r'\1\2',
            html_content, flags=_re.DOTALL
        )
    
    # Извлечь <style> блоки из шаблона и перенести в <head>
    style_blocks = _re.findall(r'<style[^>]*>(.*?)</style>', html_content, _re.DOTALL | _re.IGNORECASE)
    html_content_no_style = _re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=_re.DOTALL | _re.IGNORECASE)
    
    # Определяем @page правило — берём из шаблона если есть, иначе A4
    template_has_page = '@page' in ''.join(style_blocks)
    default_page_css = '' if template_has_page else '@page { size: A4; margin: 15mm; }'
    
    template_styles = '\n'.join(style_blocks)

    # Добавить CSS стили для печати
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Документ {template_type} #{order_id}</title>
        <style>
            {default_page_css}
            @media print {{
                body {{
                    print-color-adjust: exact;
                    -webkit-print-color-adjust: exact;
                }}
                .no-print {{
                    display: none !important;
                }}
            }}
            body {{
                font-family: Arial, sans-serif;
                color: #000;
                background: #fff;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 10px 0;
            }}
            td, th {{
                border: 1px solid #000;
                padding: 8px;
            }}
            .print-button {{
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 10px 20px;
                background: #1890ff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                z-index: 1000;
            }}
            .print-button:hover {{
                background: #40a9ff;
            }}
            .title-line strong {{
                font-size: 200%;
            }}
        </style>
        <style>
            {template_styles}
        </style>
    </head>
    <body>
        <button class="no-print print-button" onclick="window.print()">🖨️ Печать / Сохранить в PDF</button>
        {html_content_no_style}
    </body>
    </html>
    """
    
    from fastapi.responses import HTMLResponse
    
    _get_or_create_document(session, order_id, template_type, f"{template_type}_{order_id}.html", current_user)
    
    return HTMLResponse(content=full_html, media_type="text/html")


def _validate_filepath(filepath: str) -> str:
    """Проверить что файл находится в директории документов (безопасность)"""
    abs_path = os.path.abspath(filepath)
    abs_docs = os.path.abspath(DOCUMENTS_DIR)
    if not abs_path.startswith(abs_docs):
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="Файл не найден")
    return abs_path


def _save_document_record(
    session: Session,
    order_id: int,
    document_type: str,
    filename: str,
    user: User,
) -> Document:
    """Сохранить запись о сгенерированном документе"""
    doc = Document(
        order_id=order_id,
        document_type=document_type,
        filename=filename,
        status="generated",
        created_by=user.id,
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc


def _get_or_create_document(
    session: Session,
    order_id: int,
    document_type: str,
    filename: str,
    user: User,
) -> Document:
    """Получить существующую запись или создать новую"""
    # Ищем существующую запись с таким же типом и заказом
    existing = session.exec(
        select(Document).where(
            Document.order_id == order_id,
            Document.document_type == document_type,
        )
    ).first()

    if existing:
        existing.filename = filename
        existing.status = "generated"
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing

    return _save_document_record(session, order_id, document_type, filename, user)


# === СПИСОК ВСЕХ ДОКУМЕНТОВ ===

@router.get("/", summary="Список всех документов")
def list_all_documents(
    document_type: Optional[str] = Query(None, description="Тип документа"),
    status: Optional[str] = Query(None, description="Статус"),
    order_id: Optional[int] = Query(None, description="ID заказа"),
    date_from: Optional[str] = Query(None, description="Дата от (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Дата до (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Поиск по клиенту/заказу"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить список всех сгенерированных документов с фильтрацией"""
    query = select(Document)

    if document_type:
        query = query.where(Document.document_type == document_type)
    if status:
        query = query.where(Document.status == status)
    if order_id:
        query = query.where(Document.order_id == order_id)
    if date_from:
        query = query.where(Document.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.where(Document.created_at <= datetime.fromisoformat(date_to + "T23:59:59"))

    # Общее количество
    count_query = select(func.count(Document.id)).select_from(query.subquery())
    total = session.exec(count_query).one()

    # Пагинация
    query = query.order_by(Document.created_at.desc()).offset(skip).limit(limit)
    documents = session.exec(query).all()

    # Обогащаем данными о заказе
    results = []
    for doc in documents:
        order = session.get(Order, doc.order_id)
        results.append({
            "id": doc.id,
            "order_id": doc.order_id,
            "document_type": doc.document_type,
            "filename": doc.filename,
            "status": doc.status,
            "created_at": doc.created_at.isoformat(),
            "created_by": doc.created_by,
            "sent_at": doc.sent_at.isoformat() if doc.sent_at else None,
            "notes": doc.notes,
            "order": {
                "client_name": order.client_name if order else "—",
                "client_phone": order.client_phone if order else "—",
                "device_model": f"{order.device_brand} {order.device_model}" if order else "—",
                "total_cost": order.total_cost if order else 0,
                "status": order.status if order else "—",
            } if order else None,
        })

    return {"items": results, "total": total}


@router.patch("/{doc_id}/status", summary="Обновить статус документа")
def update_document_status(
    doc_id: int,
    data: dict,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Обновить статус документа (generated/sent/signed/cancelled)"""
    doc = session.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")

    new_status = data.get("status")
    valid_statuses = ["generated", "sent", "signed", "cancelled"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Недопустимый статус. Допустимые: {valid_statuses}")

    doc.status = new_status
    if new_status == "sent" and not doc.sent_at:
        doc.sent_at = datetime.now()
    if data.get("notes") is not None:
        doc.notes = data["notes"]

    session.add(doc)
    session.commit()
    session.refresh(doc)

    logger.info(f"Статус документа #{doc_id} изменён на {new_status}")

    return {"id": doc.id, "status": doc.status, "sent_at": doc.sent_at}


@router.delete("/{doc_id}", summary="Удалить документ")
def delete_document(
    doc_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Удалить документ (запись и файл)"""
    doc = session.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Документ не найден")

    # Удаляем файл
    filepath = os.path.join(DOCUMENTS_DIR, doc.filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    # Удаляем запись
    session.delete(doc)
    session.commit()

    logger.info(f"Документ #{doc_id} удалён")
    return {"message": "Документ удалён"}


# === СТАРЫЕ ENDPOINTS ГЕНЕРАЦИИ (обновлены) ===


@router.post("/receipt/{order_id}", summary="Сгенерировать квитанцию")
def generate_receipt(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Сгенерировать квитанцию приёма для заказа"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    try:
        service = DocumentService(session)
        filepath = service.generate_receipt(order)
        filename = os.path.basename(filepath)

        # Сохраняем запись в БД
        _get_or_create_document(session, order_id, "receipt", filename, current_user)

        logger.info(f"Квитанция сгенерирована для заказа #{order_id}")
        return {"filepath": filepath, "filename": filename}
    except Exception as e:
        logger.error(f"Ошибка генерации квитанции: {e}")
        raise HTTPException(status_code=500, detail="Ошибка генерации документа")


@router.post("/diagnostic-act/{order_id}", summary="Сгенерировать акт диагностики")
def generate_diagnostic_act(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Сгенерировать акт диагностики"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    try:
        service = DocumentService(session)
        filepath = service.generate_diagnostic_act(order)
        filename = os.path.basename(filepath)

        # Сохраняем запись в БД
        _get_or_create_document(session, order_id, "diagnostic_act", filename, current_user)

        return {"filepath": filepath, "filename": filename}
    except Exception as e:
        logger.error(f"Ошибка генерации акта диагностики: {e}")
        raise HTTPException(status_code=500, detail="Ошибка генерации документа")


@router.post("/work-act/{order_id}", summary="Сгенерировать акт выполненных работ")
def generate_work_act(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Сгенерировать акт выполненных работ (при выдаче)"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    try:
        service = DocumentService(session)
        filepath = service.generate_work_act(order)
        filename = os.path.basename(filepath)

        # Сохраняем запись в БД
        _get_or_create_document(session, order_id, "work_act", filename, current_user)

        return {"filepath": filepath, "filename": filename}
    except Exception as e:
        logger.error(f"Ошибка генерации акта работ: {e}")
        raise HTTPException(status_code=500, detail="Ошибка генерации документа")


@router.post("/invoice/{order_id}", summary="Сгенерировать счёт для юрлица")
def generate_invoice(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Сгенерировать счёт для юридического лица"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    try:
        service = DocumentService(session)
        filepath = service.generate_invoice(order)
        filename = os.path.basename(filepath)

        # Сохраняем запись в БД
        _get_or_create_document(session, order_id, "invoice", filename, current_user)

        return {"filepath": filepath, "filename": filename}
    except Exception as e:
        logger.error(f"Ошибка генерации счёта: {e}")
        raise HTTPException(status_code=500, detail="Ошибка генерации документа")


@router.post("/from-template/{order_id}/{template_type}", summary="Сгенерировать из шаблона")
def generate_from_template(
    order_id: int,
    template_type: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Сгенерировать документ и сразу отдать PDF"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    try:
        service = DocumentService(session)

        # Сначала проверяем, есть ли назначенный шаблон
        from models.document_template import DocumentTemplate
        from models.document_template_assignment import DocumentTemplateAssignment
        
        assignment = session.exec(
            select(DocumentTemplateAssignment)
            .where(DocumentTemplateAssignment.document_type == template_type)
            .where(DocumentTemplateAssignment.is_active == True)
        ).first()
        
        template = None
        if assignment:
            template = session.get(DocumentTemplate, assignment.template_id)
            logger.info(f"Найден назначенный шаблон ID={assignment.template_id} для {template_type}")
        else:
            # Если нет назначения, ищем шаблон по типу
            template = session.exec(
                select(DocumentTemplate).where(DocumentTemplate.type == template_type)
            ).first()
            logger.info(f"Назначения нет, используем шаблон по типу: {template_type}")

        logger.info(f"Запрос документа: template_type={template_type}, template_found={'Да' if template else 'Нет'}")

        if template:
            # Используем шаблон из БД
            logger.info(f"Используем шаблон из БД для {template_type}")
            filepath = service.generate_from_template(template_type, order, template.content_template)
        else:
            # Fallback: используем жёсткие генераторы для известных типов
            logger.info(f"Шаблон не найден, используем fallback генератор для {template_type}")
            generators = {
                'receipt': service.generate_receipt,
                'diagnostic_act': service.generate_diagnostic_act,
                'work_act': service.generate_work_act,
                'invoice': service.generate_invoice,
            }

            if template_type in generators:
                filepath = generators[template_type](order)
            else:
                raise HTTPException(status_code=404, detail=f"Шаблон '{template_type}' не найден и генератор не существует")

        filename = os.path.basename(filepath)
        abs_path = os.path.abspath(filepath)

        # Сохраняем запись в БД
        from models.document import Document
        doc = session.exec(
            select(Document).where(
                Document.order_id == order_id,
                Document.document_type == template_type,
            )
        ).first()
        
        if doc:
            doc.filename = filename
            doc.status = "generated"
        else:
            doc = Document(
                order_id=order_id,
                document_type=template_type,
                filename=filename,
                status="generated",
                created_by=current_user.id,
            )
        session.add(doc)
        session.commit()

        # Возвращаем JSON с информацией о файле
        return {"filepath": filepath, "filename": filename}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка генерации из шаблона: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")


@router.get("/download", summary="Скачать PDF документ")
def download_document(
    filename: str = Query(..., description="Имя файла для скачивания"),
    token: Optional[str] = Query(None, description="JWT токен для авторизации"),
    session: Session = Depends(get_session),
):
    """
    Скачать сгенерированный PDF документ.
    Открывать в новой вкладке: GET /api/documents/download?filename=receipt_1.pdf&token=xxx
    """
    from core.security import decode_token
    
    if token:
        try:
            payload = decode_token(token)
            username: str = payload.get("sub")
            if username:
                user = session.exec(select(User).where(User.username == username)).first()
                if not user:
                    raise HTTPException(status_code=401, detail="Пользователь не найден")
        except Exception:
            raise HTTPException(status_code=401, detail="Неверный токен")
    else:
        raise HTTPException(status_code=401, detail="Требуется токен авторизации (параметр ?token=)")
    
    filepath = os.path.join(DOCUMENTS_DIR, filename)
    abs_path = _validate_filepath(filepath)

    return FileResponse(
        path=abs_path,
        filename=filename,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )


@router.get("/list/{order_id}", summary="Список документов заказа")
def list_order_documents(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Получить список сгенерированных документов для заказа"""
    if not os.path.exists(DOCUMENTS_DIR):
        return []

    files = []
    for fname in os.listdir(DOCUMENTS_DIR):
        if f"_{order_id}_" in fname and fname.endswith('.pdf'):
            filepath = os.path.join(DOCUMENTS_DIR, fname)
            files.append({
                "filename": fname,
                "size": os.path.getsize(filepath),
                "type": fname.split('_')[0],
                "url": f"/api/documents/download?filename={fname}",
            })

    return files
