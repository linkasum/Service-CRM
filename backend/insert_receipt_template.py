#!/usr/bin/env python3
"""Сохранить HTML-шаблон квитанции в БД"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session, select, create_engine
from core.config import get_settings

RECEIPT_HTML = '''<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
@media print {
  @page { size: 210mm 330mm; margin: 8mm 10mm; }
  body { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
  .no-print { display: none !important; }
}
body {
  font-family: Arial, sans-serif;
  font-size: 9pt;
  line-height: 1.3;
  color: #000;
  background: #fff;
  width: 190mm;
}
.upper-part {
  font-size: 9pt;
  padding-bottom: 4mm;
}
.upper-part .title-line {
  font-size: 11pt;
  font-weight: bold;
  margin-bottom: 2mm;
}
.upper-part .company-line {
  margin-bottom: 1mm;
}
.upper-part .info-block {
  margin: 2mm 0;
}
.upper-part .info-row {
  margin: 1mm 0;
}
.upper-part .conditions-title {
  font-weight: bold;
  margin: 2mm 0 1mm 0;
  font-size: 8.5pt;
}
.upper-part .conditions-list {
  font-size: 7.5pt;
  line-height: 1.25;
  padding-left: 12px;
  margin-bottom: 2mm;
}
.upper-part .conditions-list li {
  margin-bottom: 1.5px;
}
.upper-part .sign-block {
  margin-top: 2mm;
  font-size: 8.5pt;
}
.upper-part .sign-row {
  margin: 1.5mm 0;
}
.upper-part .status-block {
  margin-top: 2mm;
  border-top: 1px dashed #999;
  padding-top: 2mm;
  font-size: 8.5pt;
}

/* Линия отреза */
.cut-line {
  border-top: 2px dashed #555;
  margin: 3mm 0;
  position: relative;
  text-align: left;
}
.cut-line::before {
  content: "✂";
  position: absolute;
  top: -9px;
  left: 0;
  background: white;
  padding-right: 3px;
  font-size: 12pt;
  color: #555;
}

/* Нижняя часть */
.lower-part {
  font-size: 7.5pt;
  line-height: 1.25;
}
.lower-part .title-line {
  font-size: 9pt;
  font-weight: bold;
  margin-bottom: 1.5mm;
}
.lower-part .company-line {
  margin-bottom: 0.8mm;
}
.lower-part .info-block {
  margin: 1.5mm 0;
}
.lower-part .info-row {
  margin: 0.8mm 0;
}
.lower-part .conditions-title {
  font-weight: bold;
  margin: 1.5mm 0 0.8mm 0;
  font-size: 7pt;
}
.lower-part .conditions-list {
  font-size: 6.5pt;
  line-height: 1.2;
  padding-left: 10px;
  margin-bottom: 1.5mm;
}
.lower-part .conditions-list li {
  margin-bottom: 1px;
}
.lower-part .sign-block {
  margin-top: 1.5mm;
  font-size: 7pt;
}
.lower-part .sign-row {
  margin: 1mm 0;
}
.lower-part .master-block {
  margin: 1.5mm 0;
  padding: 1.5mm;
  border: 1px solid #ccc;
  font-size: 7.5pt;
}
.lower-part .master-block .master-row {
  margin: 1mm 0;
}
</style>

<!-- ВЕРХНЯЯ ЧАСТЬ — для клиента -->
<div class="upper-part">
  <div class="title-line">Приёмная квитанция &nbsp;&nbsp; №{order_id} от {order_date}</div>
  <div class="company-line"><strong>{company_name}</strong>, {company_address}</div>
  <div class="company-line">{company_phone}</div>

  <div class="info-block">
    <div class="info-row"><strong>Клиент:</strong> {client_name}, {client_phone}</div>
    <div class="info-row"><strong>Устройство:</strong> {device_category}, {device_brand} {device_model}, {serial_number}</div>
    <div class="info-row"><strong>Внешний вид:</strong> {appearance}</div>
    <div class="info-row"><strong>Комплектация:</strong> {accessories}</div>
    <div class="info-row"><strong>Неисправность со слов клиента:</strong> {complaint}</div>
  </div>

  <div class="conditions-title">Условия оказания услуг:</div>
  <ol class="conditions-list">
    <li>Диагностика является отдельной, необходимой для проведения ремонта услугой. Диагностика производится полностью бесплатно, даже в случае отказа от дальнейшего ремонта. Срок диагностики аппарата составляет от 2 до 5 рабочих дней, который может быть увеличен в зависимости от ее сложности или необходимости применения специального оборудования.</li>
    <li>СЦ имеет право ОТКАЗАТЬ клиенту в ремонте аппарата, при невозможности ремонта, отсутствии необходимых запчастей или оборудования, или выявленных в процессе ремонта дополнительных неисправностей, или обнаружения следов жизнедеятельности.</li>
    <li>ГАРАНТИЙНОЕ ОБСЛУЖИВАНИЕ распространяется только на ремонт заявленной неисправности и при наличии неповреждённого гарантийного стикера. Гарантия на ремонт аппаратов, попавших под воздействие агрессивной среды (воды и т.д.), имеющие внешние, внутренние повреждения, или видимые деформации корпуса, составляет 3 дня (на проверку). Стоимость РАСШИРЕНИЯ ГАРАНТИИ до трех месяцев составляет 20% от стоимости ремонта.</li>
    <li>При проведении ремонта с использованием запчасти, ЗАМЕНЕННАЯ ЗАПЧАСТЬ предоставляется клиенту по требованию заранее, до проведения ремонта (если замененная запасть не разрушилась при снятии).</li>
    <li>Срок хранения аппарата в мастерской составляет до 2 месяцев с момента сдачи в ремонт, после которого отправляется на склад платного временного хранения, где может быть утилизирована либо реализована с целью компенсации расходов на хранение.</li>
    <li>Данная квитанция является гарантийным талоном и СОБСТВЕННОСТЬЮ сервисного центра ВЫДАЕТСЯ в случае проведенного ремонта.</li>
    <li>В связи с отсутствием полной проверки функционала сдаваемого в ремонт аппарата, КЛИЕНТ ОЗНАКОМЛЕН и СОГЛАСЕН с возможностью выявления ДОПОЛНИТЕЛЬНЫХ НЕИСПРАВНОСТЕЙ, обнаруженных в ходе или после ремонта.</li>
    <li>Выдача техники производится по квитанции сервисного центра. При отсутствии квитанции технику получает владелец, указанный в квитанции, по паспорту.</li>
  </ol>

  <div class="sign-block">
    <div class="sign-row">Менеджер: __________________</div>
    <div class="sign-row">С условиями оказания услуг ознакомлен и согласен &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Заказчик: __________________ {client_name}</div>
  </div>

  <div class="status-block">
    <div class="info-row"><strong>Статус заказа</strong></div>
    <div class="info-row">Дата: {created_at}</div>
    <div class="info-row">Устройство получил(а), претензий по ремонту не имею, комплектацию и внешний вид проверил(а)</div>
    <div class="info-row">Заказчик: __________________ {client_name}</div>
  </div>
</div>

<!-- ЛИНИЯ ОТРЕЗА -->
<div class="cut-line"></div>

<!-- НИЖНЯЯ ЧАСТЬ — для сервиса -->
<div class="lower-part">
  <div class="title-line">Приёмная квитанция &nbsp; №{order_id} от {order_date}</div>
  <div class="company-line"><strong>{company_name}</strong>, {company_address}</div>
  <div class="company-line">{company_phone}</div>

  <div class="master-block">
    <div class="master-row">Мастер: _______________</div>
    <div class="master-row">Выполненные работы: _______________</div>
    <div class="master-row">Сумма ремонта: _______________</div>
  </div>

  <div class="info-block">
    <div class="info-row"><strong>Клиент:</strong> {client_name}, {client_phone}</div>
    <div class="info-row"><strong>Устройство:</strong> {device_category}, {device_brand} {device_model}, {serial_number}</div>
    <div class="info-row"><strong>Внешний вид:</strong> {appearance}</div>
    <div class="info-row"><strong>Комплектация:</strong> {accessories}</div>
    <div class="info-row"><strong>Неисправность со слов клиента:</strong> {complaint}</div>
  </div>

  <div class="conditions-title">Условия оказания услуг:</div>
  <ol class="conditions-list">
    <li>Диагностика является отдельной, необходимой для проведения ремонта услугой. Диагностика производится полностью бесплатно, даже в случае отказа от дальнейшего ремонта. Срок диагностики аппарата составляет от 2 до 5 рабочих дней, который может быть увеличен в зависимости от ее сложности или необходимости применения специального оборудования.</li>
    <li>СЦ имеет право ОТКАЗАТЬ клиенту в ремонте аппарата, при невозможности ремонта, отсутствии необходимых запчастей или оборудования, или выявленных в процессе ремонта дополнительных неисправностей, или обнаружения следов жизнедеятельности.</li>
    <li>ГАРАНТИЙНОЕ ОБСЛУЖИВАНИЕ распространяется только на ремонт заявленной неисправности и при наличии неповреждённого гарантийного стикера. Гарантия на ремонт аппаратов, попавших под воздействие агрессивной среды (воды и т.д.), имеющие внешние, внутренние повреждения, или видимые деформации корпуса, составляет 3 дня (на проверку). Стоимость РАСШИРЕНИЯ ГАРАНТИИ до трех месяцев составляет 20% от стоимости ремонта.</li>
    <li>При проведении ремонта с использованием запчасти, ЗАМЕНЕННАЯ ЗАПЧАСТЬ предоставляется клиенту по требованию заранее, до проведения ремонта (если замененная запасть не разрушилась при снятии).</li>
    <li>Срок хранения аппарата в мастерской составляет до 2 месяцев с момента сдачи в ремонт, после которого отправляется на склад платного временного хранения, где может быть утилизирована либо реализована с целью компенсации расходов на хранение.</li>
    <li>Данная квитанция является гарантийным талоном и СОБСТВЕННОСТЬЮ сервисного центра ВЫДАЕТСЯ в случае проведенного ремонта.</li>
    <li>В связи с отсутствием полной проверки функционала сдаваемого в ремонт аппарата, КЛИЕНТ ОЗНАКОМЛЕН и СОГЛАСЕН с возможностью выявления ДОПОЛНИТЕЛЬНЫХ НЕИСПРАВНОСТЕЙ, обнаруженных в ходе или после ремонта.</li>
    <li>Выдача техники производится по квитанции сервисного центра. При отсутствии квитанции технику получает владелец, указанный в квитанции, по паспорту.</li>
  </ol>

  <div class="sign-block">
    <div class="sign-row">Менеджер: __________________</div>
    <div class="sign-row">С условиями оказания услуг ознакомлен и согласен &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Заказчик: __________________ {client_name}</div>
    <div class="sign-row">Дата: {created_at}</div>
    <div class="sign-row">Устройство получил(а), претензий по ремонту не имею, комплектацию и внешний вид проверил(а)</div>
    <div class="sign-row">Заказчик: __________________ {client_name}</div>
  </div>
</div>'''

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)

with Session(engine) as session:
    import psycopg2
    conn = psycopg2.connect(settings.DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute("SELECT id FROM document_templates WHERE type = 'receipt'")
    row = cur.fetchone()
    
    if row:
        cur.execute(
            "UPDATE document_templates SET content_template = %s, updated_at = NOW() WHERE type = 'receipt'",
            (RECEIPT_HTML,)
        )
        print(f"Updated existing receipt template (id={row[0]})")
    else:
        cur.execute(
            "INSERT INTO document_templates (type, content_template, updated_at) VALUES (%s, %s, NOW())",
            ('receipt', RECEIPT_HTML)
        )
        print("Inserted new receipt template")
    
    conn.commit()
    cur.close()
    conn.close()
    print("Done.")
