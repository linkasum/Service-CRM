"""
Сервис импорта данных: клиенты, запчасти, заказы
"""

import csv
import io
import os
import tempfile
import logging
from datetime import datetime
from typing import Dict, List, Any
from sqlmodel import Session, select

from models.client import Client
from models.part import Part
from models.order import Order

logger = logging.getLogger(__name__)

try:
    import openpyxl
except:
    openpyxl = None


def parse_csv(content, encoding=None):
    if encoding:
        text = content.decode(encoding)
    else:
        text = content.decode("utf-8")
    sep = "," if "," in text[:100] else ";" if ";" in text[:100] else "\t"
    reader = csv.DictReader(io.StringIO(text), delimiter=sep)
    headers = [h.strip() for h in reader.fieldnames] if reader.fieldnames else []
    rows = []
    for row in reader:
        rows.append({k.strip(): v.strip() if v else "" for k, v in row.items()})
    return headers, rows


def parse_xlsx(content):
    if not openpyxl:
        raise Exception("openpyxl not installed")
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        f.write(content)
        path = f.name
    try:
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        headers = next(rows_iter, None)
        if not headers:
            return [], []
        headers = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(headers)]
        rows = []
        for row in rows_iter:
            rows.append({headers[i]: str(v).strip() if v is not None else "" for i, v in enumerate(row)})
        return headers, rows
    finally:
        os.unlink(path)


def parse_uploaded_file(content, filename, encoding=None):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in ("xlsx", "xls"):
        return parse_xlsx(content)
    return parse_csv(content, encoding)


def validate_field_mapping(headers, field_mapping, import_type):
    errors = []
    cleaned = {}
    for k, v in field_mapping.items():
        if v and str(v).strip():
            cleaned[k] = str(v).strip()
    if not cleaned:
        return ["Сопоставьте хотя бы одно поле"]
    if import_type == "clients":
        if not cleaned.get("client_name") and not cleaned.get("client_phone"):
            errors.append("Нужно сопоставить ФИО или Телефон")
    return errors


FIELD_MAPPINGS = {
    "clients": {"fields": {"client_name": "ФИО", "client_phone": "Телефон"}},
    "parts": {
        "required": ["name"],
        "fields": {
            "name": "Название", "article": "Артикул",
            "quantity": "Количество", "cost_price": "Себестоимость",
            "sale_price": "Цена продажи",
        },
    },
    "orders": {
        "fields": {
            "order_number": "Заказ (номер)",
            "order_type": "Тип заказа",
            "status": "Статус",
            "created_at": "Создан",
            "manager_name": "Менеджер",
            "client_name": "Клиент",
            "client_phone": "Телефон",
            "client_type": "Юридическое лицо",
            "age_group": "Возраст клиента",
            "source": "Откуда узнал",
            "device_category": "Вид устройства",
            "device_brand": "Бренд",
            "device_model": "Модель",
            "serial_number": "IMEI / SN",
            "accessories": "Комплектация",
            "appearance": "Внешний вид",
            "complaint": "Причина обращения",
            "is_warranty": "По гарантии",
            "has_delivery": "Доставка",
            "total_cost": "Позиции цена",
            "parts_cost": "Товары цена",
            "work_cost": "Услуги цена",
            "paid_amount": "Платежи",
        },
    },
}


def parse_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    date_str = str(date_str).strip()
    for fmt in ["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S",
                "%d.%m.%Y %H:%M", "%d/%m/%Y %H:%M"]:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def map_status(status_str: str) -> str:
    s = (status_str or "").strip().lower()
    status_map = {
        "новый": "new", "new": "new",
        "диагностика": "diagnostics", "diagnostics": "diagnostics",
        "согласован": "agreed", "agreed": "agreed",
        "в ремонте": "repair", "repair": "repair",
        "готов": "ready", "ready": "ready",
        "на выдаче": "ready_pickup", "ready_pickup": "ready_pickup",
        "выдан": "issued", "issued": "issued",
        "отменен": "cancelled", "отменён": "cancelled", "cancelled": "cancelled",
    }
    return status_map.get(s, "new")


def import_orders(session, rows, field_mapping):
    stats = {"created": 0, "errors": 0, "skipped": 0, "duplicates": 0}

    def v(row, key):
        col = field_mapping.get(key, "")
        return str(row.get(col, "")).strip() if col else ""

    for row in rows:
        try:
            name = v(row, "client_name")
            phone = v(row, "client_phone")
            if not name and not phone:
                stats["skipped"] += 1
                continue

            phone = phone[:20]
            order_number = v(row, "order_number") or None
            device_brand = v(row, "device_brand")
            device_model = v(row, "device_model")

            existing = session.exec(
                select(Order).where(
                    Order.client_phone == phone,
                    Order.device_brand == device_brand,
                    Order.device_model == device_model,
                )
            ).first()
            if existing:
                if order_number:
                    existing.order_number = order_number
                    session.add(existing)
                stats["duplicates"] += 1
                continue

            created_at = parse_date(v(row, "created_at")) or datetime.now()
            issued_at = parse_date(v(row, "issued_at"))

            total_cost = 0.0
            try: total_cost = float(v(row, "total_cost") or 0)
            except: pass
            parts_cost = 0.0
            try: parts_cost = float(v(row, "parts_cost") or 0)
            except: pass
            work_cost = 0.0
            try: work_cost = float(v(row, "work_cost") or 0)
            except: pass
            paid_amount = 0.0
            try: paid_amount = float(v(row, "paid_amount") or 0)
            except: pass

            is_warranty = v(row, "is_warranty").lower() in ("да", "yes", "1", "true")
            has_delivery = v(row, "has_delivery").lower() in ("да", "yes", "1", "true")
            client_type = "company" if v(row, "client_type").lower() in ("юр", "юридическое", "company", "юр. лицо") else "individual"

            order = Order(
                order_number=order_number,
                order_type=v(row, "order_type") or None,
                status=map_status(v(row, "status")),
                client_name=name or "Клиент",
                client_phone=phone,
                client_type=client_type,
                age_group=v(row, "age_group") or None,
                source=v(row, "source") or None,
                manager_name=v(row, "manager_name") or None,
                device_brand=device_brand,
                device_model=device_model,
                device_category=v(row, "device_category") or "phone",
                serial_number=v(row, "serial_number") or None,
                accessories=v(row, "accessories") or None,
                appearance=v(row, "appearance") or None,
                complaint=v(row, "complaint") or "",
                is_warranty=is_warranty,
                has_delivery=has_delivery,
                total_cost=total_cost,
                parts_cost=parts_cost,
                work_cost=work_cost,
                paid_amount=paid_amount,
                created_at=created_at,
                issued_at=issued_at,
            )
            session.add(order)
            stats["created"] += 1
        except Exception as e:
            logger.error(f"Ошибка импорта заказа: {e}")
            stats["errors"] += 1

    session.commit()
    return stats


def import_clients(session, rows, field_mapping):
    def v(r, k): 
        col = field_mapping.get(k, "")
        return str(r.get(col, "")).strip() if col else ""
    stats = {"created": 0, "errors": 0, "skipped": 0}
    for row in rows:
        try:
            name = v(row, "client_name") or "Клиент"
            phone = v(row, "client_phone")
            if not name and not phone:
                stats["skipped"] += 1
                continue
            phone = phone[:20]
            existing = session.exec(select(Client).where(Client.phone == phone)).first()
            if existing:
                stats["skipped"] += 1
                continue
            client = Client(name=name[:300], phone=phone, created_at=datetime.now().isoformat())
            session.add(client)
            stats["created"] += 1
        except Exception:
            stats["errors"] += 1
    session.commit()
    return stats


def import_parts(session, rows, field_mapping):
    def v(r, k):
        col = field_mapping.get(k, "")
        return str(r.get(col, "")).strip() if col else ""
    stats = {"created": 0, "errors": 0}
    for row in rows:
        try:
            name = v(row, "name")
            if not name:
                continue
            part = Part(
                name=name,
                article=v(row, "article") or "",
                quantity=int(v(row, "quantity") or 0) or 0,
                cost_price=float(v(row, "cost_price") or 0) or 0,
                sale_price=float(v(row, "sale_price") or 0) or 0,
            )
            session.add(part)
            stats["created"] += 1
        except Exception:
            stats["errors"] += 1
    session.commit()
    return stats


IMPORT_HANDLERS = {
    "clients": import_clients,
    "parts": import_parts,
    "orders": import_orders,
}
