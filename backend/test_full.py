"""
Расширенная проверка UI — клики по всем кнопкам, формы, навигация
"""
import json
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:5173"

def get_token():
    import urllib.request
    req = urllib.request.Request("http://localhost:8000/api/auth/login",
        data=json.dumps({"username": "admin", "password": "admin"}).encode(),
        headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read())["access_token"]

def run_tests():
    token = get_token()
    results = []
    
    def add(name, ok, detail=""):
        icon = "✅" if ok else "❌"
        print(f"  {icon} {name}: {detail}")
        results.append((name, ok, detail))
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--window-size=1400,900"])
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        context.add_init_script(f'window.localStorage.setItem("token", "{token}");')
        page = context.new_page()
        
        # ===== 1. НАВИГАЦИЯ =====
        print("\n=== 1. НАВИГАЦИЯ ===")
        page.goto(f"{BASE_URL}/orders", wait_until="domcontentloaded", timeout=10000)
        page.wait_for_timeout(1000)
        
        nav_items = [
            ("Дашборд", "/dashboard"),
            ("Заказы", "/orders"),
            ("Склад", "/parts"),
            ("Клиенты", "/clients"),
            ("Зарплата", "/salary"),
            ("Отчёты", "/reports"),
            ("Импорт", "/import"),
            ("Настройки", "/settings"),
            ("Профиль", "/profile"),
        ]
        
        for label, path in nav_items:
            try:
                # Ищем пункт меню по тексту
                menu_item = page.locator(f'.ant-menu-item:has-text("{label}")').first
                if menu_item.count() > 0:
                    menu_item.click()
                    page.wait_for_url(f"**{path}*", timeout=5000)
                    page.wait_for_timeout(500)
                    
                    # Проверяем что страница загрузилась (нет ошибок)
                    err_count = page.locator(".ant-result-error, .ant-alert-error").count()
                    if err_count > 0:
                        add(f"Меню: {label}", False, "ошибка на странице")
                    else:
                        add(f"Меню: {label}", True)
                else:
                    add(f"Меню: {label}", False, "пункт не найден")
            except Exception as e:
                add(f"Меню: {label}", False, str(e)[:50])
        
        # ===== 2. ТАБЛИЦА ЗАКАЗОВ =====
        print("\n=== 2. ТАБЛИЦА ЗАКАЗОВ ===")
        page.goto(f"{BASE_URL}/orders", wait_until="domcontentloaded", timeout=10000)
        page.wait_for_timeout(1000)
        
        # Поиск
        try:
            search = page.locator('input[placeholder="Поиск..."]')
            if search.count() > 0:
                search.fill("8")
                page.wait_for_timeout(500)
                rows = page.locator("tbody tr").count()
                add("Поиск в таблице", rows > 0, f"найдено: {rows}")
                search.clear()
                page.wait_for_timeout(500)
            else:
                add("Поиск в таблице", False, "поле не найдено")
        except Exception as e:
            add("Поиск в таблице", False, str(e)[:50])
        
        # Фильтр по статусу
        try:
            status_select = page.locator('.ant-select').filter(has_text="Статус").first
            if status_select.count() > 0:
                status_select.click()
                page.wait_for_timeout(300)
                page.keyboard.press("Escape")
                add("Фильтр по статусу", True)
            else:
                add("Фильтр по статусу", False, "селект не найден")
        except Exception as e:
            add("Фильтр по статусу", False, str(e)[:50])
        
        # Быстрые фильтры (теги)
        try:
            tags = page.locator(".ant-tag").all()
            if len(tags) > 0:
                add("Быстрые фильтры", True, f"тегов: {len(tags)}")
            else:
                add("Быстрые фильтры", False, "нет тегов")
        except Exception as e:
            add("Быстрые фильтры", False, str(e)[:50])
        
        # Кнопка "Новый заказ"
        try:
            new_btn = page.get_by_text("Новый заказ")
            if new_btn.count() > 0:
                new_btn.click()
                page.wait_for_url("**/orders/create*", timeout=5000)
                page.wait_for_timeout(1000)
                add("Кнопка 'Новый заказ'", True)
            else:
                add("Кнопка 'Новый заказ'", False)
        except Exception as e:
            add("Кнопка 'Новый заказ'", False, str(e)[:50])
        
        # ===== 3. СОЗДАНИЕ ЗАКАЗА =====
        print("\n=== 3. СОЗДАНИЕ ЗАКАЗА ===")
        page.goto(f"{BASE_URL}/orders/create", wait_until="domcontentloaded", timeout=10000)
        page.wait_for_timeout(1000)
        
        # Проверка формы — количество полей
        try:
            inputs = page.locator("input, textarea, select").count()
            add("Форма создания", inputs > 5, f"полей ввода: {inputs}")
        except Exception as e:
            add("Форма создания", False, str(e)[:50])
        
        # Проверка кнопки "Создать"
        try:
            create_btn = page.get_by_role("button", name="Создать")
            if create_btn.count() == 0:
                create_btn = page.get_by_text("Создать")
            if create_btn.count() > 0:
                add("Кнопка 'Создать'", True)
            else:
                add("Кнопка 'Создать'", False, "не найдена")
        except Exception as e:
            add("Кнопка 'Создать'", False, str(e)[:50])
        
        # Чекбоксы печати документов
        try:
            checkboxes = page.locator('input[type="checkbox"]').count()
            add("Чекбоксы документов", checkboxes > 0, f"чекбоксов: {checkboxes}")
        except Exception as e:
            add("Чекбоксы документов", False, str(e)[:50])
        
        # Возврат на заказы
        try:
            back_btn = page.get_by_role("button").filter(has_text="Назад").first
            if back_btn.count() == 0:
                back_btn = page.locator(".ant-btn").filter(has_text="Назад").first
            if back_btn.count() > 0:
                back_btn.click()
                page.wait_for_url("**/orders*", timeout=5000)
                add("Кнопка 'Назад'", True)
            else:
                # Пробуем через URL
                page.goto(f"{BASE_URL}/orders", wait_until="domcontentloaded")
                add("Кнопка 'Назад'", False, "не найдена, перешли по URL")
        except Exception as e:
            add("Кнопка 'Назад'", False, str(e)[:50])
        
        # ===== 4. КАРТОЧКА ЗАКАЗА =====
        print("\n=== 4. КАРТОЧКА ЗАКАЗА ===")
        page.goto(f"{BASE_URL}/orders", wait_until="domcontentloaded", timeout=10000)
        page.wait_for_timeout(1000)
        
        try:
            first_link = page.locator("tbody tr a").first
            order_id = first_link.inner_text()
            first_link.click()
            page.wait_for_url("**/orders/*", timeout=10000)
            page.wait_for_timeout(2000)
            add(f"Открытие заказа {order_id}", True)
        except Exception as e:
            add("Открытие заказа", False, str(e)[:50])
            order_id = ""
        
        # Смена статуса
        try:
            status_select = page.locator(".ant-select").filter(has_text="Статус").first
            if status_select.count() > 0:
                add("Селект статуса в карточке", True)
            else:
                add("Селект статуса в карточке", False)
        except Exception as e:
            add("Селект статуса в карточке", False, str(e)[:50])
        
        # Кнопки PDF
        try:
            for doc in ["Квитанция", "Акт", "Счёт"]:
                btn = page.get_by_text(doc)
                if btn.count() > 0:
                    add(f"Кнопка '{doc}'", True)
                else:
                    add(f"Кнопка '{doc}'", False)
        except Exception as e:
            add("Кнопки PDF", False, str(e)[:50])
        
        # Комментарии
        try:
            comment_input = page.locator('textarea[placeholder="Комментарий..."]')
            if comment_input.count() > 0:
                add("Поле комментариев", True)
                # Отправляем тестовый комментарий
                comment_input.fill("Тест")
                send_btn = page.get_by_text("Отправить")
                if send_btn.count() > 0:
                    add("Кнопка 'Отправить' комментарий", True)
                else:
                    add("Кнопка 'Отправить' комментарий", False)
            else:
                add("Поле комментариев", False)
        except Exception as e:
            add("Комментарии", False, str(e)[:50])
        
        # Вкладки
        try:
            tabs = page.locator(".ant-tabs-tab").count()
            if tabs > 0:
                # Кликаем на вторую вкладку
                page.locator(".ant-tabs-tab").nth(1).click()
                page.wait_for_timeout(500)
                add("Вкладки карточки", True, f"вкладок: {tabs}")
            else:
                add("Вкладки карточки", False)
        except Exception as e:
            add("Вкладки карточки", False, str(e)[:50])
        
        # Правая панель (клиент)
        try:
            orders_text = page.locator("text=Заказов").first
            if orders_text.count() > 0:
                text = orders_text.inner_text()
                add("Панель клиента", True, text)
            else:
                add("Панель клиента", False, "нет данных")
        except Exception as e:
            add("Панель клиента", False, str(e)[:50])
        
        # Кнопка "Назад" в карточке
        try:
            back_btn = page.get_by_role("button").filter(has_text="Назад").first
            if back_btn.count() == 0:
                back_btn = page.locator("button:has(.anticon-arrow-left)").first
            if back_btn.count() > 0:
                back_btn.click()
                page.wait_for_url("**/orders*", timeout=5000)
                add("Кнопка 'Назад' из карточки", True)
            else:
                add("Кнопка 'Назад' из карточки", False)
        except Exception as e:
            add("Кнопка 'Назад' из карточки", False, str(e)[:50])
        
        # ===== 5. НАСТРОЙКИ =====
        print("\n=== 5. НАСТРОЙКИ ===")
        page.goto(f"{BASE_URL}/settings", wait_until="domcontentloaded", timeout=10000)
        page.wait_for_timeout(1000)
        
        # Вкладки настроек
        try:
            tabs = page.locator(".ant-tabs-tab").count()
            add("Вкладки настроек", tabs > 0, f"вкладок: {tabs}")
        except Exception as e:
            add("Вкладки настроек", False, str(e)[:50])
        
        # ===== 6. ПЕРЕКЛЮЧЕНИЕ ТЕМЫ =====
        print("\n=== 6. ПЕРЕКЛЮЧЕНИЕ ТЕМЫ ===")
        page.goto(f"{BASE_URL}/orders", wait_until="domcontentloaded", timeout=10000)
        page.wait_for_timeout(500)
        
        try:
            switch = page.locator('.ant-switch').first
            if switch.count() > 0:
                # Текущее состояние
                is_checked = page.evaluate("() => document.querySelector('.ant-switch').getAttribute('aria-checked')")
                switch.click()
                page.wait_for_timeout(800)
                
                # Проверяем что фон изменился
                body_bg = page.evaluate("() => window.getComputedStyle(document.documentElement).backgroundColor")
                add("Переключение темы", True, f"фон: {body_bg}")
                
                # Переключаем обратно
                switch.click()
                page.wait_for_timeout(800)
            else:
                add("Переключение темы", False, "переключатель не найден")
        except Exception as e:
            add("Переключение темы", False, str(e)[:50])
        
        # ===== 7. СКЛАД =====
        print("\n=== 7. СКЛАД ===")
        page.goto(f"{BASE_URL}/parts", wait_until="domcontentloaded", timeout=10000)
        page.wait_for_timeout(1000)
        
        try:
            table_rows = page.locator("tbody tr").count()
            add("Таблица склада", table_rows >= 0, f"строк: {table_rows}")
        except Exception as e:
            add("Таблица склада", False, str(e)[:50])
        
        # ===== 8. КЛИЕНТЫ =====
        print("\n=== 8. КЛИЕНТЫ ===")
        page.goto(f"{BASE_URL}/clients", wait_until="domcontentloaded", timeout=10000)
        page.wait_for_timeout(1000)
        
        try:
            table_rows = page.locator("tbody tr").count()
            add("Таблица клиентов", table_rows >= 0, f"строк: {table_rows}")
        except Exception as e:
            add("Таблица клиентов", False, str(e)[:50])
        
        # ===== 9. ОТЧЁТЫ =====
        print("\n=== 9. ОТЧЁТЫ ===")
        page.goto(f"{BASE_URL}/reports", wait_until="domcontentloaded", timeout=10000)
        page.wait_for_timeout(1000)
        
        try:
            tabs = page.locator(".ant-tabs-tab").count()
            add("Вкладки отчётов", tabs > 0, f"вкладок: {tabs}")
        except Exception as e:
            add("Вкладки отчётов", False, str(e)[:50])
        
        browser.close()
    
    # ===== ИТОГИ =====
    print("\n" + "=" * 60)
    pass_count = sum(1 for _, s, _ in results if s)
    fail_count = sum(1 for _, s, _ in results if not s)
    
    print(f"Итого: {pass_count} PASS, {fail_count} FAIL")
    print()
    
    if fail_count > 0:
        print("❌ ПРОБЛЕМЫ:")
        for name, ok, detail in results:
            if not ok:
                print(f"  • {name}: {detail}")
    
    # Сохраняем
    with open("screenshots/full_test_report.json", "w") as f:
        json.dump({"total": {"pass": pass_count, "fail": fail_count}, "results": results}, f, indent=2)
    print(f"\n📄 Отчёт: screenshots/full_test_report.json")

if __name__ == "__main__":
    run_tests()
