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
    
    # Заполняем поля
    page.fill('input[placeholder*="+7"]', '+79991234567')
    page.wait_for_timeout(300)
    page.fill('input[placeholder*="Иванов"]', 'Тестов Тест')
    page.wait_for_timeout(300)
    
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
    
    # Ошибки валидации
    errors = page.locator('.ant-form-item-explain-error').all_inner_texts()
    print(f'  Errors: {errors if errors else "None"}')
    
    # Нажимаем Создать
    page.locator('button', has_text='Создать').click()
    page.wait_for_timeout(3000)
    
    url = page.url
    msgs = page.locator('.ant-message-notice-content').all_inner_texts()
    print(f'  URL: {url}')
    print(f'  Messages: {msgs}')
    
    page.screenshot(path='screenshots/create_test.png', full_page=True)
    browser.close()
    print('Done')
