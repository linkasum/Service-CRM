#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import json

token = json.load(open('/tmp/token.json'))['access_token']

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--window-size=1400,900'])
    context = browser.new_context(viewport={'width':1400, 'height':900})
    context.add_init_script(f'window.localStorage.setItem("token","{token}");')
    page = context.new_page()
    
    page.goto('http://localhost:5173/orders/create', wait_until='domcontentloaded', timeout=10000)
    page.wait_for_timeout(1500)
    
    # 1. Вводим телефон существующего клиента
    page.fill('input[placeholder*="+7"]', '+79993333333')
    page.wait_for_timeout(1000)
    
    # Проверяем автозаполнение имени
    name_val = page.evaluate('''() => {
        const inputs = document.querySelectorAll('input');
        for(const inp of inputs) {
            if(inp.placeholder && inp.placeholder.includes('Иванов')) {
                return inp.value;
            }
        }
        return '';
    }''')
    print(f'  Автозаполнение имени: "{name_val}" {"✅" if name_val else "❌"}')
    
    # 2. Заполняем остальные поля
    # Вид устройства
    page.locator('.ant-select-selector').first.click()
    page.wait_for_timeout(300)
    page.locator('.ant-select-item-option').first.click()
    page.wait_for_timeout(300)
    
    # Бренд
    page.locator('.ant-select-selector').nth(1).click()
    page.wait_for_timeout(300)
    page.locator('.ant-select-item-option').first.click()
    page.wait_for_timeout(300)
    
    # Модель
    page.fill('input[placeholder*="iPhone"]', 'iPhone 14')
    page.wait_for_timeout(300)
    
    # Описание проблемы
    page.locator('textarea[placeholder*="Не включается"]').fill('Разбит экран')
    page.wait_for_timeout(300)
    
    # 3. Проверяем ошибки валидации
    errors = page.locator('.ant-form-item-explain-error').all_inner_texts()
    print(f'  Ошибки валидации: {errors if errors else "Нет ✅"}')
    
    # 4. Нажимаем Создать
    page.locator('button', has_text='Создать').click()
    page.wait_for_timeout(3000)
    
    # 5. Что произошло?
    url = page.url
    msgs = page.locator('.ant-message-notice-content').all_inner_texts()
    print(f'  URL после создания: {url}')
    print(f'  Сообщения: {msgs}')
    
    if '/orders/' in url and url != 'http://localhost:5173/orders/create':
        print('  ✅ Заказ создан успешно!')
    else:
        print('  ❌ Заказ не создан')
    
    page.screenshot(path='screenshots/create_full_test.png', full_page=True)
    browser.close()
    print('Done')
