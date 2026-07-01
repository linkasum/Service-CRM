#!/usr/bin/env python3
"""Тест добавления услуги в заказ через браузер"""
import urllib.request, json
from playwright.sync_api import sync_playwright

req = urllib.request.Request('http://localhost:8000/api/auth/login',
    data=json.dumps({'username':'admin','password':'admin'}).encode(),
    headers={'Content-Type':'application/json'})
token = json.loads(urllib.request.urlopen(req).read())['access_token']

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--window-size=1400,900'])
    context = browser.new_context(viewport={'width':1400,'height':900})
    context.add_init_script(f'window.localStorage.setItem("token","{token}");')
    page = context.new_page()
    
    print('=== Шаг 1: Идём в заказ #8 ===')
    page.goto('http://localhost:5173/orders/8', wait_until='domcontentloaded', timeout=10000)
    page.wait_for_timeout(2000)
    
    # Проверяем текущее состояние
    before = page.evaluate('''() => {
        const cards = document.querySelectorAll('[class*="ant-card"]');
        for(const c of cards) {
            if(c.textContent.includes('Товары и услуги')) {
                return {
                    text: c.textContent.substring(0, 500),
                    hasItems: c.querySelectorAll('table').length > 0
                };
            }
        }
        return { text: 'не найдено', hasItems: false };
    }''')
    print(f'  До: {before["hasItems"]}')
    print(f'  Текст: {before["text"][:200]}')
    
    print('\n=== Шаг 2: Кликаем "+ Услуга" ===')
    uslug_btn = page.evaluate('''() => {
        const btns = document.querySelectorAll('button');
        for(const b of btns) {
            if(b.textContent.includes('+ Услуга') || (b.textContent.includes('Услуга') && b.textContent.includes('+'))) { 
                b.click(); 
                return true; 
            }
        }
        return false;
    }''')
    print(f'  Кликнули: {uslug_btn}')
    page.wait_for_timeout(1000)
    
    # Проверяем модалку
    modal_open = page.evaluate('() => document.querySelectorAll(".ant-modal").length > 0')
    print(f'  Модалка открыта: {modal_open}')
    
    page.screenshot(path='screenshots/debug_service_modal.png')
    print('  📸 screenshots/debug_service_modal.png')
    
    if not modal_open:
        # Пробуем другой подход — ищем кнопку по тексту
        page.evaluate('''() => {
            const allEls = document.querySelectorAll('*');
            for(const el of allEls) {
                if(el.textContent && el.textContent.trim().includes('+ Услуга')) {
                    console.log('Found button:', el.tagName, el.className);
                    el.click();
                    return;
                }
            }
        }''')
        page.wait_for_timeout(1000)
        modal_open = page.evaluate('() => document.querySelectorAll(".ant-modal").length > 0')
        print(f'  Модалка открыта (повтор): {modal_open}')
    
    print('\n=== Шаг 3: Выбираем услугу "Замена экрана" ===')
    if modal_open:
        # Кликаем на селект
        page.evaluate('''() => {
            const selects = document.querySelectorAll('.ant-select');
            for(const s of selects) {
                if(s.textContent.includes('Услуга') || s.closest('.ant-form-item-label')?.textContent.includes('Услуга')) {
                    s.click();
                    return;
                }
            }
        }''')
        page.wait_for_timeout(500)
        
        # Кликаем на опцию "Замена экрана"
        page.evaluate('''() => {
            const options = document.querySelectorAll('.ant-select-item-option');
            for(const o of options) {
                if(o.textContent.includes('Замена экрана')) {
                    o.click();
                    return;
                }
            }
        }''')
        page.wait_for_timeout(500)
        
        # Кликаем OK
        page.evaluate('''() => {
            const btns = document.querySelectorAll('.ant-modal-footer button, [class*="modal"] button');
            for(const b of btns) {
                if(b.textContent.includes('OK') || b.textContent.includes('ОК')) {
                    b.click();
                    return;
                }
            }
        }''')
        page.wait_for_timeout(2000)
        
        # Проверяем результат
        after = page.evaluate('''() => {
            const cards = document.querySelectorAll('[class*="ant-card"]');
            for(const c of cards) {
                if(c.textContent.includes('Товары и услуги')) {
                    return {
                        text: c.textContent.substring(0, 800),
                        hasServiceItems: c.textContent.includes('Замена экрана') || c.textContent.includes('УСЛУГИ'),
                        tables: c.querySelectorAll('table').length
                    };
                }
            }
            return { text: 'не найдено', hasServiceItems: false, tables: 0 };
        }''')
        print(f'  После: таблицы={after["tables"]}, есть услуга={after["hasServiceItems"]}')
        print(f'  Текст: {after["text"][:400]}')
        
        page.screenshot(path='screenshots/debug_after_service.png')
        print('  📸 screenshots/debug_after_service.png')
    else:
        print('  ❌ Модалка не открылась!')
    
    # Проверяем API напрямую
    print('\n=== Шаг 4: Проверка API напрямую ===')
    api_req = urllib.request.Request(f'http://localhost:8000/api/orders/8',
        headers={'Authorization': f'Bearer {token}'})
    r = urllib.request.urlopen(api_req, timeout=5)
    order = json.loads(r.read())
    print(f'  service_items: {order.get("service_items", "N/A")}')
    print(f'  parts: {order.get("parts", "N/A")}')
    print(f'  work_cost: {order.get("work_cost")}')
    print(f'  total_cost: {order.get("total_cost")}')
    
    browser.close()
