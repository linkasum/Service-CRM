#!/usr/bin/env python3
from playwright.sync_api import sync_playwright
import json

token = json.load(open('/tmp/token.json'))['access_token']

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--window-size=1400,900'])
    context = browser.new_context(viewport={'width': 1400, 'height': 900})
    context.add_init_script('window.localStorage.setItem("token", "' + token + '");')
    page = context.new_page()
    
    page.goto('http://localhost:5173/cash', wait_until='networkidle', timeout=10000)
    page.wait_for_timeout(1000)
    
    # Click ready tab
    page.locator('.ant-tabs-tab:has-text("На выдаче")').click()
    page.wait_for_timeout(1000)
    
    # Check for pay button
    pay_btn = page.locator('button:has-text("Оплатить")')
    print(f'Pay buttons: {pay_btn.count()}')
    
    if pay_btn.count() > 0:
        pay_btn.first.click()
        page.wait_for_timeout(1500)
        
        modal = page.locator('.ant-modal')
        print(f'Modal open: {modal.count() > 0}')
        
        if modal.count() > 0:
            title = page.locator('.ant-modal-title').inner_text()
            print(f'Modal title: {title}')
            
            has_cash = page.locator('text="Наличные"').count() > 0
            has_card = page.locator('text="Карта"').count() > 0
            has_receipt = page.locator('text="Квитанция"').count() > 0
            print(f'Cash option: {has_cash}')
            print(f'Card option: {has_card}')
            print(f'Receipt checkbox: {has_receipt}')
    
    page.screenshot(path='screenshots/pay_test.png')
    browser.close()
    print('Done')
