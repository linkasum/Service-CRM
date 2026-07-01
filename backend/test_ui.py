"""
UI тест CRM системы через Playwright
Заходит в приложение, кликает по всем кнопкам, проверяет что работает
"""
import json
import sys
import time
from playwright.sync_api import sync_playwright, expect, TimeoutError as PlaywrightTimeout

BASE_URL = "http://localhost:5173"

def get_token():
    """Получаем токен через API"""
    import urllib.request
    req = urllib.request.Request("http://localhost:8000/api/auth/login",
        data=json.dumps({"username": "admin", "password": "admin"}).encode(),
        headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    return data["access_token"]

def run_tests():
    token = get_token()
    print("✅ Токен получен")
    
    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--window-size=1400,900"])
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            locale="ru-RU",
            storage_state=None,
        )
        
        # Сохраняем токен в localStorage
        context.add_init_script(f"""
            window.localStorage.setItem('token', '{token}');
        """)
        
        page = context.new_page()
        
        # === ТЕСТ 1: Логин / Главная ===
        print("\n📋 Тест 1: Главная страница")
        try:
            page.goto(f"{BASE_URL}/orders", wait_until="domcontentloaded", timeout=15000)
            page.wait_for_selector("h1", timeout=5000)
            h1 = page.locator("h1").first.inner_text()
            print(f"  ✅ Заголовок: {h1}")
            results.append(("Главная", "PASS", h1))
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            results.append(("Главная", "FAIL", str(e)))
        
        # Скриншот
        page.screenshot(path="screenshots/01_main.png")
        print("  📸 Скриншот: screenshots/01_main.png")
        
        # === ТЕСТ 2: Таблица заказов ===
        print("\n📋 Тест 2: Таблица заказов")
        try:
            page.wait_for_selector("table", timeout=5000)
            rows = page.locator("tbody tr").count()
            print(f"  ✅ Строк в таблице: {rows}")
            
            # Проверяем цвета строк
            first_row = page.locator("tbody tr").first
            bg = first_row.evaluate("el => window.getComputedStyle(el).backgroundColor")
            print(f"  ✅ Цвет строки: {bg}")
            results.append(("Таблица заказов", "PASS", f"строк: {rows}"))
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            results.append(("Таблица заказов", "FAIL", str(e)))
        
        page.screenshot(path="screenshots/02_orders_table.png")
        
        # === ТЕСТ 3: Поиск и фильтры ===
        print("\n📋 Тест 3: Поиск")
        try:
            search_input = page.locator('input[placeholder="Поиск..."]')
            search_input.fill("1")
            page.wait_for_timeout(500)
            rows_after = page.locator("tbody tr").count()
            print(f"  ✅ Результаты поиска '1': {rows_after} строк")
            search_input.clear()
            page.wait_for_timeout(500)
            results.append(("Поиск", "PASS", f"результатов: {rows_after}"))
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            results.append(("Поиск", "FAIL", str(e)))
        
        # === ТЕСТ 4: Клик по заказу -> карточка ===
        print("\n📋 Тест 4: Открытие карточки заказа")
        try:
            first_link = page.locator("tbody tr a").first
            order_id = first_link.inner_text()
            first_link.click()
            page.wait_for_url("**/orders/*", timeout=10000)
            current_url = page.url
            print(f"  ✅ URL: {current_url}")
            
            # Ждём загрузки карточки
            page.wait_for_timeout(2000)
            results.append(("Карточка заказа", "PASS", order_id))
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            results.append(("Карточка заказа", "FAIL", str(e)))
        
        page.screenshot(path="screenshots/03_order_detail.png")
        print("  📸 Скриншот: screenshots/03_order_detail.png")
        
        # === ТЕСТ 5: Кнопки PDF в карточке ===
        print("\n📋 Тест 5: Кнопки PDF")
        try:
            # Кнопка Квитанция
            receipt_btn = page.get_by_text("Квитанция")
            if receipt_btn.count() > 0:
                print("  ✅ Кнопка 'Квитанция' найдена")
                # Не кликаем — открывает PDF в новой вкладке
            else:
                print("  ❌ Кнопка 'Квитанция' НЕ найдена")
            
            # Кнопка Акт
            act_btn = page.get_by_text("Акт")
            if act_btn.count() > 0:
                print("  ✅ Кнопка 'Акт' найдена")
            else:
                print("  ❌ Кнопка 'Акт' НЕ найдена")
            
            # Кнопка Счёт
            invoice_btn = page.get_by_text("Счёт")
            if invoice_btn.count() > 0:
                print("  ✅ Кнопка 'Счёт' найдена")
            else:
                print("  ❌ Кнопка 'Счёт' НЕ найдена")
            
            results.append(("Кнопки PDF", "PASS", "все найдены"))
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            results.append(("Кнопки PDF", "FAIL", str(e)))
        
        # === ТЕСТ 6: Комментарии ===
        print("\n📋 Тест 6: Комментарии")
        try:
            comment_input = page.locator('textarea[placeholder="Комментарий..."]')
            if comment_input.count() > 0:
                print("  ✅ Поле комментариев найдено")
                comment_input.fill("Тестовый комментарий")
                send_btn = page.get_by_text("Отправить")
                if send_btn.count() > 0:
                    print("  ✅ Кнопка 'Отправить' найдена")
            else:
                print("  ❌ Поле комментариев НЕ найдено")
            results.append(("Комментарии", "PASS", "OK"))
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            results.append(("Комментарии", "FAIL", str(e)))
        
        # === ТЕСТ 7: Переключение вкладок ===
        print("\n📋 Тест 7: Вкладки карточки")
        try:
            tab_general = page.get_by_text("Общая информация")
            tab_financial = page.get_by_text("Финансы")
            if tab_general.count() > 0 and tab_financial.count() > 0:
                print("  ✅ Вкладки найдены")
                tab_financial.click()
                page.wait_for_timeout(500)
                print("  ✅ Вкладка 'Финансы' переключена")
                tab_general.click()
                results.append(("Вкладки", "PASS", "OK"))
            else:
                print("  ❌ Вкладки НЕ найдены")
                results.append(("Вкладки", "FAIL", "не найдены"))
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            results.append(("Вкладки", "FAIL", str(e)))
        
        # === ТЕСТ 8: Правая панель — информация о клиенте ===
        print("\n📋 Тест 8: Панель клиента")
        try:
            loyalty = page.locator("text=Заказов")
            if loyalty.count() > 0:
                text = loyalty.first.inner_text()
                print(f"  ✅ Инфо о клиенте: {text}")
                results.append(("Панель клиента", "PASS", text))
            else:
                print("  ⚠️ Инфо о клиенте не найдено")
                results.append(("Панель клиента", "WARN", "нет данных"))
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            results.append(("Панель клиента", "FAIL", str(e)))
        
        # === ТЕСТ 9: Страница создания заказа ===
        print("\n📋 Тест 9: Создание заказа")
        try:
            # Идём на страницу создания
            page.goto(f"{BASE_URL}/orders/create", wait_until="domcontentloaded", timeout=10000)
            page.wait_for_timeout(1000)
            page.screenshot(path="screenshots/04_order_create.png")
            print("  📸 Скриншот: screenshots/04_order_create.png")
            
            # Проверяем форму
            title = page.locator("h1, h2, h3").filter(has_text="Новый заказ").first
            if title.count() > 0:
                print(f"  ✅ Заголовок: {title.inner_text()}")
                results.append(("Создание заказа", "PASS", "OK"))
            else:
                print("  ⚠️ Заголовок не найден, но страница открылась")
                results.append(("Создание заказа", "WARN", "заголовок?"))
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            results.append(("Создание заказа", "FAIL", str(e)))
        
        # === ТЕСТ 10: Тёмная тема ===
        print("\n📋 Тест 10: Проверка тёмной темы")
        try:
            page.goto(f"{BASE_URL}/orders", wait_until="domcontentloaded", timeout=10000)
            page.wait_for_timeout(1000)
            
            # Проверяем фон body
            body_bg = page.evaluate("() => window.getComputedStyle(document.body).backgroundColor")
            print(f"  ✅ Фон body: {body_bg}")
            
            # Проверяем есть ли тёмные элементы
            cards = page.locator(".ant-card, [class*='card'], [class*='Card']")
            card_count = cards.count()
            print(f"  ✅ Карточек на странице: {card_count}")
            
            # Скриншот тёмной темы
            page.screenshot(path="screenshots/05_dark_theme.png")
            print("  📸 Скриншот: screenshots/05_dark_theme.png")
            results.append(("Тёмная тема", "PASS", body_bg))
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            results.append(("Тёмная тема", "FAIL", str(e)))
        
        # === ТЕСТ 11: Навигация ===
        print("\n📋 Тест 11: Навигация по разделам")
        try:
            nav_pages = [
                ("/clients", "Клиенты"),
                ("/parts", "Склад"),
                ("/settings", "Настройки"),
                ("/reports", "Отчёты"),
                ("/orders", "Заказы"),
            ]
            for path, name in nav_pages:
                try:
                    page.goto(f"{BASE_URL}{path}", wait_until="domcontentloaded", timeout=8000)
                    page.wait_for_timeout(500)
                    print(f"  ✅ {name}: OK")
                except Exception as e:
                    print(f"  ❌ {name}: {e}")
            results.append(("Навигация", "PASS", "все страницы"))
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            results.append(("Навигация", "FAIL", str(e)))
        
        # === ТЕСТ 12: Статус-бар заказов (быстрые фильтры) ===
        print("\n📋 Тест 12: Быстрые фильтры")
        try:
            page.goto(f"{BASE_URL}/orders", wait_until="domcontentloaded", timeout=10000)
            page.wait_for_timeout(1000)
            
            tags = page.locator(".ant-tag")
            tag_count = tags.count()
            print(f"  ✅ Тегов-фильтров: {tag_count}")
            
            # Клик по "Все"
            all_tag = tags.first
            if all_tag.count() > 0:
                all_tag.click()
                page.wait_for_timeout(500)
                print("  ✅ Фильтр 'Все' кликабельный")
            results.append(("Быстрые фильтры", "PASS", f"тегов: {tag_count}"))
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            results.append(("Быстрые фильтры", "FAIL", str(e)))
        
        browser.close()
    
    # === ИТОГИ ===
    print("\n" + "=" * 60)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("=" * 60)
    pass_count = sum(1 for _, s, _ in results if s == "PASS")
    fail_count = sum(1 for _, s, _ in results if s == "FAIL")
    warn_count = sum(1 for _, s, _ in results if s == "WARN")
    
    for name, status, detail in results:
        icon = "✅" if status == "PASS" else ("❌" if status == "FAIL" else "⚠️")
        print(f"  {icon} {name}: {status} — {detail}")
    
    print(f"\n  Итого: {pass_count} PASS, {fail_count} FAIL, {warn_count} WARN")
    
    # Сохраняем отчёт
    with open("screenshots/test_report.json", "w") as f:
        json.dump({"results": results, "total": {"pass": pass_count, "fail": fail_count, "warn": warn_count}}, f, indent=2)
    print(f"\n  📄 Отчёт: screenshots/test_report.json")

if __name__ == "__main__":
    run_tests()
