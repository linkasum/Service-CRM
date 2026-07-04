"""
Сервис генерации PDF документов
Использует reportlab с поддержкой кириллицы
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import Session, select
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from models.order import Order
from models.company_settings import CompanySettings
from models.document_template import DocumentTemplate
from models.user import User
from core.config import get_settings
from core.logging import logger


def clean_html_simple(html: str) -> str:
    """Очистить HTML для PDF"""
    import re

    # Заменить <br> на перенос
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    # Удалить пустые параграфы
    html = re.sub(r"<p></p>", "", html)
    # Удалить все теги
    html = re.sub(r"<[^>]+>", "", html)
    # Удалить лишние переносы
    html = re.sub(r"\n\n+", "\n", html)
    return html.strip()


settings = get_settings()

# Пути к шрифтам (поддержка кириллицы)
FONTS_DIR = os.path.join(os.path.dirname(__file__), "..", "fonts")
DOCUMENTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "documents")

# Регистрация кириллического шрифта
# Для работы нужен шрифт с поддержкой кириллицы
# Используем встроенный шрифт как fallback
CYRILLIC_FONT = "Helvetica"  # Заменить на "DejaVuSans" или аналогичный при наличии


class DocumentService:
    """Сервис для генерации PDF документов"""

    def __init__(self, session: Session):
        self.session = session

    def _register_fonts(self):
        """Зарегистрировать кириллические шрифты"""
        font_path = os.path.join(FONTS_DIR, "DejaVuSans.ttf")
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont("CyrillicFont", font_path))
                return "CyrillicFont"
            except Exception as e:
                logger.warning(f"Ошибка загрузки шрифта: {e}")
        logger.info("Используется fallback шрифт Helvetica")
        return "Helvetica"

    def _get_styles(self, font_name: str) -> Dict[str, ParagraphStyle]:
        """Получить стили для документа"""
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Title"],
            fontName=font_name,
            fontSize=16,
            textColor=HexColor("#1a1a1a"),
            alignment=TA_CENTER,
            spaceAfter=8 * mm,
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading1"],
            fontName=font_name,
            fontSize=13,
            textColor=HexColor("#333333"),
            spaceBefore=8 * mm,
            spaceAfter=4 * mm,
        )

        normal_style = ParagraphStyle(
            "CustomNormal",
            parent=styles["Normal"],
            fontName=font_name,
            fontSize=10,
            leading=13,
            spaceAfter=3 * mm,
        )

        small_style = ParagraphStyle(
            "Small",
            parent=normal_style,
            fontSize=9,
            textColor=HexColor("#555555"),
        )

        bold_style = ParagraphStyle(
            "Bold",
            parent=normal_style,
            fontName=font_name,
            fontSize=10,
        )

        return {
            "title": title_style,
            "heading": heading_style,
            "normal": normal_style,
            "small": small_style,
            "bold": bold_style,
        }

    def _build_pdf(self, elements: list, filename: str) -> str:
        """Собрать PDF из элементов"""
        os.makedirs(DOCUMENTS_DIR, exist_ok=True)
        filepath = os.path.join(DOCUMENTS_DIR, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        doc.build(elements)
        logger.info(f"PDF создан: {filepath}")
        return filepath

    def generate_receipt(self, order: Order) -> str:
        """Сгенерировать квитанцию приёма"""
        font_name = self._register_fonts()
        styles = self._get_styles(font_name)
        company = self.session.exec(select(CompanySettings)).first()

        elements = []

        # Заголовок
        elements.append(
            Paragraph(
                company.company_name if company else "Сервисный центр", styles["title"]
            )
        )
        if company and company.phone:
            elements.append(Paragraph(f"Тел: {company.phone}", styles["small"]))
        if company and company.address:
            elements.append(Paragraph(f"Адрес: {company.address}", styles["small"]))

        elements.append(Spacer(1, 10 * mm))
        elements.append(Paragraph("КВИТАНЦИЯ ПРИЁМА", styles["heading"]))

        # Данные заказа
        data = [
            ["Номер заказа:", f"#{order.id}"],
            ["Дата приёма:", order.created_at.strftime("%d.%m.%Y %H:%M")],
            ["Клиент:", order.client_name],
            ["Телефон:", order.client_phone],
            ["Устройство:", order.device_model],
            ["Серийный номер:", order.serial_number or "—"],
            ["Неисправность:", order.complaint],
        ]

        if order.total_cost:
            data.append(["Предварительная сумма:", f"{order.total_cost:.2f} руб."])

        table = Table(data, colWidths=[60 * mm, 110 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), font_name),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LINEBELOW", (0, 0), (0, -1), 0.5, HexColor("#cccccc")),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 15 * mm))

        # Подпись
        elements.append(Paragraph("_" * 40, styles["normal"]))
        elements.append(Paragraph("Подпись клиента", styles["small"]))

        filename = f"receipt_{order.id}_{order.created_at.strftime('%Y%m%d')}.pdf"
        return self._build_pdf(elements, filename)

    def generate_diagnostic_act(self, order: Order) -> str:
        """Сгенерировать акт диагностики"""
        font_name = self._register_fonts()
        styles = self._get_styles(font_name)
        company = self.session.exec(select(CompanySettings)).first()

        elements = []

        elements.append(
            Paragraph(
                company.company_name if company else "Сервисный центр", styles["title"]
            )
        )
        elements.append(Spacer(1, 10 * mm))
        elements.append(Paragraph("АКТ ДИАГНОСТИКИ", styles["heading"]))

        data = [
            ["Номер заказа:", f"#{order.id}"],
            ["Устройство:", order.device_model],
            ["Серийный номер:", order.serial_number or "—"],
            ["Клиент:", order.client_name],
        ]

        table = Table(data, colWidths=[60 * mm, 110 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), font_name),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LINEBELOW", (0, 0), (0, -1), 0.5, HexColor("#cccccc")),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 8 * mm))

        elements.append(Paragraph("Выявленные дефекты:", styles["heading"]))
        elements.append(
            Paragraph(order.diagnostic_act_text or "Не указаны", styles["normal"])
        )

        if order.total_cost:
            elements.append(Spacer(1, 8 * mm))
            elements.append(
                Paragraph(
                    f"Рекомендуемая стоимость ремонта: <b>{order.total_cost:.2f} руб.</b>",
                    styles["normal"],
                )
            )

        filename = (
            f"diagnostic_act_{order.id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        return self._build_pdf(elements, filename)

    def generate_work_act(self, order: Order) -> str:
        """Сгенерировать акт выполненных работ (при выдаче) — по макету act.png"""
        font_name = self._register_fonts()
        styles = self._get_styles(font_name)
        company = self.session.exec(select(CompanySettings)).first()
        now = datetime.now()
        acceptor = (
            self.session.get(User, order.acceptor_id) if order.acceptor_id else None
        )
        client_first = order.client_name.split(" ")[0] if order.client_name else "—"

        elements = []

        # ===== ШАПКА: Заголовок слева + Компания справа =====
        header_data = [
            [
                Paragraph(
                    f"<b><font size='14'>Акт выполненных работ</font></b><br/>Заказ №{order.id} от {order.created_at.strftime('%d.%m.%Y')}",
                    styles["normal"],
                ),
                Paragraph(
                    f"<b>{company.company_name if company else 'Сервисный центр'}</b><br/>{company.address or ''}<br/>{company.phone or ''}",
                    ParagraphStyle(
                        "RightAlign", parent=styles["normal"], alignment=TA_RIGHT
                    ),
                ),
            ]
        ]
        header_table = Table(header_data, colWidths=[90 * mm, 90 * mm])
        header_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5 * mm),
                ]
            )
        )
        elements.append(header_table)

        elements.append(Spacer(1, 3 * mm))

        # ===== ТАБЛИЦА КЛИЕНТА =====
        client_data = [
            [
                Paragraph("<b>Клиент</b>", styles["normal"]),
                f"{client_first}, {order.client_phone}",
            ],
            [
                Paragraph("<b>Устройство</b>", styles["normal"]),
                f"{order.device_brand} {order.device_model},",
            ],
            [Paragraph("<b>Внешний вид</b>", styles["normal"]), "б/у"],
            [
                Paragraph("<b>Комплектация</b>", styles["normal"]),
                order.accessories.lower() if order.accessories else "—",
            ],
            [
                Paragraph("<b>Неисправность</b>", styles["normal"]),
                order.complaint or "—",
            ],
        ]

        client_table = Table(client_data, colWidths=[35 * mm, 145 * mm])
        client_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), font_name),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#000000")),
                ]
            )
        )
        elements.append(client_table)

        elements.append(Spacer(1, 5 * mm))

        # ===== ТАБЛИЦА РАБОТ (запчасти + услуги) =====
        work_header = [
            "№",
            "Позиция",
            "Артикул",
            "Гарантия, дн.",
            "Цена, ₽",
            "Скидка, ₽",
            "Количество",
            "Сумма, ₽",
        ]

        # Собираем строки: запчасти + услуги
        work_rows = []
        row_num = 1

        # Запчасти
        for part in order.parts or []:
            part_name = part.part.name if part.part else part.part_name
            work_rows.append(
                [
                    str(row_num),
                    f"📦 {part_name}",
                    "—",
                    str(order.warranty_days or 30),
                    f"{part.price_at_order:.2f}",
                    "0.00",
                    str(part.quantity),
                    f"{part.price_at_order * part.quantity:.2f}",
                ]
            )
            row_num += 1

        # Услуги
        for svc in order.service_items or []:
            work_rows.append(
                [
                    str(row_num),
                    f"🔧 {svc.service_name}",
                    "—",
                    str(order.warranty_days or 30),
                    f"{svc.price_at_order:.2f}",
                    "0.00",
                    str(svc.quantity),
                    f"{svc.price_at_order * svc.quantity:.2f}",
                ]
            )
            row_num += 1

        # Если ничего нет — пустая строка
        if not work_rows:
            work_rows = [[""] * 8]

        # Итого
        total_sum = order.total_cost or 0
        work_rows.append(
            [""] * 6
            + [
                Paragraph(
                    "<b>Сумма, ₽</b>",
                    ParagraphStyle(
                        "TotalH", fontName=font_name, fontSize=10, alignment=TA_RIGHT
                    ),
                ),
                Paragraph(
                    f"<b>{total_sum:.2f}</b>",
                    ParagraphStyle(
                        "TotalV", fontName=font_name, fontSize=10, alignment=TA_RIGHT
                    ),
                ),
            ]
        )

        work_table = Table(
            work_rows,
            colWidths=[
                10 * mm,
                45 * mm,
                20 * mm,
                22 * mm,
                20 * mm,
                20 * mm,
                20 * mm,
                23 * mm,
            ],
        )
        work_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), font_name),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#000000")),
                    ("BACKGROUND", (-2, -1), (-1, -1), HexColor("#f0f0f0")),
                ]
            )
        )
        elements.append(work_table)

        elements.append(Spacer(1, 5 * mm))

        # ===== УСЛОВИЯ ГАРАНТИИ =====
        elements.append(
            Paragraph("<b>Условия гарантийного обслуживания</b>", styles["normal"])
        )
        elements.append(Spacer(1, 3 * mm))

        warranty_text = (
            "<b>1.</b> ГАРАНТИЙНОЕ ОБСЛУЖИВАНИЕ распространяется только на ремонт заявленной неисправности "
            "и при наличии неповреждённого гарантийного стикера. Гарантия на ремонт аппаратов, попавших под "
            "воздействие агрессивной среды (воды и т.д.), имеющие внешние, внутренние повреждения, "
            "или видимые деформации корпуса, составляет 3 дня (на проверку). Стоимость РАСШИРЕНИЯ ГАРАНТИИ "
            "до трех месяцев составляет 20% от стоимости ремонта."
        )
        elements.append(Paragraph(warranty_text, styles["normal"]))

        elements.append(Spacer(1, 8 * mm))

        # ===== ПОДПИСИ =====
        sig_data = [
            [
                Paragraph(f"<b>Менеджер:</b> {'_' * 25}", styles["normal"]),
                Paragraph(
                    f"<b>Заказчик:</b> {'_' * 20} {client_first}<br/>"
                    f"<font size='9'>с условиями гарантийного обслуживания ознакомлен и согласен</font>",
                    ParagraphStyle(
                        "SigRight", parent=styles["normal"], alignment=TA_RIGHT
                    ),
                ),
            ]
        ]
        sig_table = Table(sig_data, colWidths=[90 * mm, 90 * mm])
        sig_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        elements.append(sig_table)

        elements.append(Spacer(1, 5 * mm))

        # ===== ДАТА =====
        elements.append(
            Paragraph(
                f"<b>Дата:</b> {now.strftime('%d.%m.%Y %H:%M')}", styles["normal"]
            )
        )

        filename = f"work_act_{order.id}_{now.strftime('%Y%m%d')}.pdf"
        return self._build_pdf(elements, filename)

    def generate_invoice(self, order: Order) -> str:
        """Сгенерировать счёт для юридических лиц"""
        font_name = self._register_fonts()
        styles = self._get_styles(font_name)
        company = self.session.exec(select(CompanySettings)).first()

        elements = []

        # Шапка с реквизитами
        elements.append(Paragraph("СЧЁТ", styles["title"]))

        if company:
            company_data = [
                ["Организация:", company.company_name],
                ["ИНН:", company.inn or "—"],
                ["Адрес:", company.address or "—"],
                ["Телефон:", company.phone or "—"],
                ["Email:", company.email or "—"],
            ]
        else:
            company_data = [["Информация о компании не настроена", ""]]

        comp_table = Table(company_data, colWidths=[50 * mm, 120 * mm])
        comp_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), font_name),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )

        elements.append(comp_table)
        elements.append(Spacer(1, 10 * mm))

        # Данные счёта
        elements.append(Paragraph(f"Счёт по заказу #{order.id}", styles["heading"]))

        invoice_data = [
            ["Клиент:", order.client_name],
            ["Телефон:", order.client_phone],
            ["Устройство:", order.device_model],
            ["Описание работ:", order.complaint],
        ]

        data_table = Table(invoice_data, colWidths=[50 * mm, 120 * mm])
        data_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), font_name),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LINEBELOW", (0, 0), (0, -1), 0.5, HexColor("#cccccc")),
                ]
            )
        )

        elements.append(data_table)
        elements.append(Spacer(1, 8 * mm))

        # Итого
        elements.append(
            Paragraph(
                f"<b>ИТОГО К ОПЛАТЕ: {order.total_cost or 0:.2f} руб.</b>",
                styles["normal"],
            )
        )

        filename = f"invoice_{order.id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        return self._build_pdf(elements, filename)

    def _parse_html_content(self, html: str, font_name: str) -> list:
        """Parse HTML content and create PDF elements with proper A4 layout"""
        import re
        from html.parser import HTMLParser

        elements = []
        styles = self._get_styles(font_name)

        # Check if HTML contains proper table structure
        if "<table" in html.lower():
            elements = self._parse_html_with_tables(html, font_name, styles)
        else:
            # Fallback to simple parsing for plain text templates
            html = re.sub(r"\s+", " ", html)
            html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
            html = re.sub(r"</p>", "\n</p>", html)
            html = re.sub(r"</tr>", "\n</tr>", html)
            html = re.sub(r"<[^>]+>", "", html)
            html = html.strip()

            lines = html.split("\n")
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if re.match(r"^\d+\.", line):
                    elements.append(Paragraph(line, styles["normal"]))
                elif any(
                    keyword in line
                    for keyword in [
                        "Менеджер",
                        "Заказчик",
                        "Устройство",
                        "Клиент",
                        "Дата",
                    ]
                ):
                    elements.append(Paragraph(f"<b>{line}</b>", styles["normal"]))
                else:
                    elements.append(Paragraph(line, styles["normal"]))

                elements.append(Spacer(1, 3))

        return elements

    def _parse_html_with_tables(self, html: str, font_name: str, styles: Dict) -> list:
        """Parse HTML with tables for proper A4 layout - improved version"""
        import re

        elements = []

        # First, handle standalone paragraphs and headers outside tables
        # Split content by tables to process non-table content
        parts = re.split(
            r"(<table[^>]*>.*?</table>)", html, flags=re.DOTALL | re.IGNORECASE
        )

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Check if it's a table
            if re.match(r"<table", part, re.IGNORECASE):
                # Parse the table
                table_result = self._parse_single_table(part, font_name, styles)
                if table_result:
                    table_data = table_result["rows"]
                    cell_styles = table_result.get("cell_styles", [])
                    col_count = len(table_data[0]) if table_data else 2
                    
                    # Calculate column widths from styles or use equal widths
                    col_widths = self._calculate_col_widths(table_data, cell_styles, col_count)
                    
                    table = Table(table_data, colWidths=col_widths)
                    table_style = [
                        ("FONTNAME", (0, 0), (-1, -1), font_name),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#000000")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 3),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ]
                    
                    # Add cell-specific styles (alignment, etc.)
                    self._apply_cell_styles(table_style, cell_styles, col_count)
                    
                    table.setStyle(TableStyle(table_style))
                    elements.append(table)
                    elements.append(Spacer(1, 3 * mm))
            else:
                # It's non-table content - process paragraphs, lists, etc.
                self._parse_inline_content(part, elements, styles)
                elements.append(Spacer(1, 2 * mm))

        return elements

    def _parse_single_table(
        self, table_html: str, font_name: str, styles: Dict
    ) -> dict:
        """Parse a single HTML table - returns dict with rows and cell_styles"""
        import re
        from html import unescape
        from html.parser import HTMLParser

        def format_cell_text(text: str) -> str:
            """Convert inline HTML formatting to ReportLab format for table cells"""
            text = unescape(text)
            # Handle bold - preserve <b> and <strong>
            text = re.sub(r'<strong>(.*?)</strong>', r'<b>\1</b>', text, flags=re.IGNORECASE)
            # Handle italic - preserve <i> and <em>
            text = re.sub(r'<em>(.*?)</em>', r'<i>\1</i>', text, flags=re.IGNORECASE)
            # Handle underline
            text = re.sub(r'<u>(.*?)</u>', r'<u>\1</u>', text, flags=re.IGNORECASE)
            # Remove remaining tags but keep formatting tags
            cleaned = re.sub(r'<(?!/?(?:b|i|u|font)\b)[^>]*>', '', text, flags=re.IGNORECASE)
            return cleaned.strip()

        def parse_style_attr(attrs: list) -> dict:
            """Parse style attribute from HTML tag"""
            result = {}
            for attr_name, attr_value in attrs:
                if attr_name == 'style' and attr_value:
                    # Parse inline styles
                    for style in attr_value.split(';'):
                        if ':' in style:
                            key, val = style.split(':', 1)
                            result[key.strip().lower()] = val.strip()
            return result

        class TableParser(HTMLParser):
            def __init__(self, styles):
                super().__init__()
                self.styles = styles
                self.rows = []
                self.current_row = []
                self.current_cell = ""
                self.in_td = False
                self.in_th = False
                self.cell_styles = []
                self.row_styles = []

            def handle_starttag(self, tag, attrs):
                if tag in ["td", "th"]:
                    self.in_td = tag == "td"
                    self.in_th = tag == "th"
                    self.current_cell = ""
                    # Store style for this cell
                    style_attrs = parse_style_attr(attrs)
                    self.cell_styles.append(style_attrs)

            def handle_endtag(self, tag):
                if tag in ["td", "th"]:
                    text = format_cell_text(self.current_cell)
                    if text:
                        self.current_row.append(Paragraph(text, styles["normal"]))
                    else:
                        self.current_row.append(Paragraph(" ", styles["normal"]))
                    self.in_td = False
                    self.in_th = False
                elif tag == "tr":
                    if self.current_row:
                        self.rows.append(self.current_row)
                        self.row_styles.append(list(self.cell_styles))
                    self.current_row = []
                    self.cell_styles = []

            def handle_data(self, data):
                if self.in_td or self.in_th:
                    self.current_cell += data

        parser = TableParser(styles)
        try:
            parser.feed(table_html)
            # Add last row if exists
            if parser.current_row:
                parser.rows.append(parser.current_row)
                parser.row_styles.append(list(parser.cell_styles))
        except Exception as e:
            import logging
            logging.error(f"Error parsing table HTML: {e}")
            return None

        return {"rows": parser.rows, "cell_styles": parser.row_styles}

    def _calculate_col_widths(self, table_data: list, cell_styles: list, col_count: int) -> list:
        """Calculate column widths based on cell styles"""
        # Try to find width percentages from first row
        if cell_styles and len(cell_styles) > 0:
            first_row_styles = cell_styles[0]
            widths = []
            for i, style in enumerate(first_row_styles):
                if 'width' in style:
                    width_val = style['width']
                    # Parse percentage like "40%"
                    if '%' in width_val:
                        try:
                            pct = float(width_val.replace('%', ''))
                            widths.append((165 * mm * pct) / 100)
                        except:
                            widths.append((165 * mm) / col_count)
                    else:
                        widths.append((165 * mm) / col_count)
                else:
                    widths.append((165 * mm) / col_count)
            
            # If we got some widths, return them
            if len(widths) == col_count and any(w > 0 for w in widths):
                return widths
        
        # Default: equal widths
        return [(165 * mm) / col_count] * col_count

    def _apply_cell_styles(self, table_style: list, cell_styles: list, col_count: int):
        """Apply cell-specific styles (alignment, etc.) to table style"""
        if not cell_styles:
            return
        
        for row_idx, row_styles in enumerate(cell_styles):
            for col_idx, style in enumerate(row_styles):
                # Handle text alignment
                if 'text-align' in style:
                    align = style['text-align'].lower()
                    if align == 'center':
                        table_style.append(("ALIGN", (col_idx, row_idx), (col_idx, row_idx), "CENTER"))
                    elif align == 'right':
                        table_style.append(("ALIGN", (col_idx, row_idx), (col_idx, row_idx), "RIGHT"))
                    else:
                        table_style.append(("ALIGN", (col_idx, row_idx), (col_idx, row_idx), "LEFT"))
                
                # Handle vertical alignment
                if 'vertical-align' in style:
                    valign = style['vertical-align'].lower()
                    if valign == 'top':
                        table_style.append(("VALIGN", (col_idx, row_idx), (col_idx, row_idx), "TOP"))
                    elif valign == 'bottom':
                        table_style.append(("VALIGN", (col_idx, row_idx), (col_idx, row_idx), "BOTTOM"))
                    else:
                        table_style.append(("VALIGN", (col_idx, row_idx), (col_idx, row_idx), "MIDDLE"))
                
                # Handle background color
                if 'background' in style or 'background-color' in style:
                    bg = style.get('background') or style.get('background-color')
                    if bg:
                        try:
                            table_style.append(("BACKGROUND", (col_idx, row_idx), (col_idx, row_idx), HexColor(bg)))
                        except:
                            pass

    def _parse_inline_content(self, html: str, elements: list, styles: Dict):
        """Parse non-table HTML content (paragraphs, lists, etc.)"""
        import re
        from html import unescape

        def format_inline_text(text: str) -> str:
            """Convert inline HTML formatting to ReportLab format"""
            # Unescape HTML entities first
            text = unescape(text)
            
            # Handle bold - preserve <b> and <strong>
            text = re.sub(r'<strong>(.*?)</strong>', r'<b>\1</b>', text, flags=re.IGNORECASE)
            
            # Handle italic - preserve <i> and <em>
            text = re.sub(r'<em>(.*?)</em>', r'<i>\1</i>', text, flags=re.IGNORECASE)
            
            # Handle underline
            text = re.sub(r'<u>(.*?)</u>', r'<u>\1</u>', text, flags=re.IGNORECASE)
            
            # Remove remaining tags but keep formatting tags
            # Keep <b>, <i>, <u>, <font>, remove others
            cleaned = re.sub(r'<(?!/?(?:b|i|u|font)\b)[^>]*>', '', text, flags=re.IGNORECASE)
            
            return cleaned.strip()

        # Handle headers
        h1_matches = re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL | re.IGNORECASE)
        for match in h1_matches:
            text = format_inline_text(match)
            if text:
                elements.append(
                    Paragraph(f"<b><font size='14'>{text}</font></b>", styles["normal"])
                )

        h2_matches = re.findall(r"<h2[^>]*>(.*?)</h2>", html, re.DOTALL | re.IGNORECASE)
        for match in h2_matches:
            text = format_inline_text(match)
            if text:
                elements.append(
                    Paragraph(f"<b><font size='12'>{text}</font></b>", styles["normal"])
                )

        h3_matches = re.findall(r"<h3[^>]*>(.*?)</h3>", html, re.DOTALL | re.IGNORECASE)
        for match in h3_matches:
            text = format_inline_text(match)
            if text:
                elements.append(
                    Paragraph(f"<b><font size='11'>{text}</font></b>", styles["normal"])
                )

        # Handle horizontal rules
        hr_matches = re.findall(r"<hr[^>]*/?>", html, re.IGNORECASE)
        if hr_matches:
            elements.append(Spacer(1, 5 * mm))
            elements.append(Paragraph("_" * 80, styles["small"]))
            elements.append(Spacer(1, 5 * mm))

        # Handle paragraphs - preserve inline formatting
        p_matches = re.findall(r"<p[^>]*>(.*?)</p>", html, re.DOTALL | re.IGNORECASE)
        for match in p_matches:
            text = format_inline_text(match)
            text = re.sub(r"\s+", " ", text)
            if text:
                elements.append(Paragraph(text, styles["normal"]))

        # Handle ordered lists with proper numbering
        ol_pattern = r"<ol[^>]*>(.*?)</ol>"
        ol_matches = re.findall(ol_pattern, html, re.DOTALL | re.IGNORECASE)
        for ol_match in ol_matches:
            li_items = re.findall(r"<li[^>]*>(.*?)</li>", ol_match, re.DOTALL | re.IGNORECASE)
            for i, li_match in enumerate(li_items, 1):
                text = format_inline_text(li_match)
                text = re.sub(r"\s+", " ", text)
                if text:
                    elements.append(Paragraph(f"{i}. {text}", styles["normal"]))

        # Handle unordered lists with bullet points
        ul_pattern = r"<ul[^>]*>(.*?)</ul>"
        ul_matches = re.findall(ul_pattern, html, re.DOTALL | re.IGNORECASE)
        for ul_match in ul_matches:
            li_items = re.findall(r"<li[^>]*>(.*?)</li>", ul_match, re.DOTALL | re.IGNORECASE)
            for li_match in li_items:
                text = format_inline_text(li_match)
                text = re.sub(r"\s+", " ", text)
                if text:
                    elements.append(Paragraph(f"• {text}", styles["normal"]))

        # Handle standalone list items (fallback for malformed HTML)
        if not ol_matches and not ul_matches:
            li_matches = re.findall(r"<li[^>]*>(.*?)</li>", html, re.DOTALL | re.IGNORECASE)
            for i, match in enumerate(li_matches, 1):
                text = format_inline_text(match)
                text = re.sub(r"\s+", " ", text)
                if text:
                    elements.append(Paragraph(f"{i}. {text}", styles["normal"]))

    def generate_from_template(
        self,
        template_type: str,
        order: Order,
        template_content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Сгенерировать документ из шаблона БД"""
        if not template_content:
            raise ValueError(f"Шаблон '{template_type}' пуст или не найден")

        # Словарь для подстановки
        ctx = {
            "order_id": str(order.id),
            "client_name": order.client_name or "",
            "client_phone": order.client_phone or "",
            "device_model": order.device_model or "",
            "device_brand": order.device_brand or "",
            "device_category": order.device_category or "",
            "serial_number": order.serial_number or "",
            "accessories": order.accessories or "",
            "complaint": order.complaint or "",
            "total_cost": f"{order.total_cost or 0:.2f}",
            "parts_cost": f"{order.parts_cost or 0:.2f}",
            "work_cost": f"{order.work_cost or 0:.2f}",
            "created_at": order.created_at.strftime("%d.%m.%Y %H:%M")
            if order.created_at
            else "",
            "order_date": order.created_at.strftime("%d.%m.%Y")
            if order.created_at
            else "",
            "issued_at": order.issued_at.strftime("%d.%m.%Y %H:%M")
            if order.issued_at
            else "—",
            "warranty_days": str(order.warranty_days or 0),
            "diagnostic_act_text": order.diagnostic_act_text or "Не указаны",
            "now": datetime.now().strftime("%d.%m.%Y"),
            "print_time": datetime.now().strftime("%H:%M"),
            "status": order.status or "",
            "master_name": order.master.username
            if order.master
            else (order.manager_name or "—"),
            "acceptor_name": order.acceptor.username if order.acceptor else "—",
        }

        # Добавить данные компании
        company = self.session.exec(select(CompanySettings)).first()
        if company:
            ctx.update(
                {
                    "company_name": company.company_name or "",
                    "company_inn": company.inn or "",
                    "company_address": company.address or "",
                    "company_phone": company.phone or "",
                    "company_email": company.email or "",
                }
            )

        if context:
            ctx.update(context)

        # Substitute variables
        content = template_content
        for key, value in ctx.items():
            content = content.replace(f"{{{key}}}", str(value))

        # Parse HTML and create PDF elements
        font_name = self._register_fonts()
        elements = self._parse_html_content(content, font_name)

        filename = (
            f"{template_type}_{order.id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        return self._build_pdf(elements, filename)
