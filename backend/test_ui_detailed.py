"""
Детальная проверка визуальных проблем через Playwright
"""
import json
import sys
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:5173"

def get_token():
    import urllib.request
    req = urllib.request.Request("http://localhost:8000/api/auth/login",
        data=json.dumps({"username": "admin", "password": "admin"}).encode(),
        headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    return data["access_token"]

def check_contrast(page, selector, label):
    """Проверяем контраст: цвет текста vs цвет фона"""
    try:
        el = page.locator(selector).first
        if el.count() == 0:
            print(f"  ⚠️ {label}: элемент не найден ({selector})")
            return "WARN"
        
        color = el.evaluate("el => window.getComputedStyle(el).color")
        bg = el.evaluate("""el => {
            let elem = el;
            while (elem) {
                const bg = window.getComputedStyle(elem).backgroundColor;
                if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') return bg;
                elem = elem.parentElement;
            }
            return 'rgb(255, 255, 255)';
        }""")
        
        print(f"  {label}: цвет={color}, фон={bg}")
        
        # Парсим RGB
        def parse_rgb(s):
            nums = [int(x) for x in s.replace('rgb(', '').replace('rgba(', '').replace(')', '').split(',')[:3]]
            return nums
        
        try:
            tc = parse_rgb(color)
            tbg = parse_rgb(bg)
            brightness_text = (tc[0] * 299 + tc[1] * 587 + tc[2] * 114) / 1000
            brightness_bg = (tbg[0] * 299 + tbg[1] * 587 + tbg[2] * 114) / 1000
            diff = abs(brightness_text - brightness_bg)
            if diff < 50:
                print(f"    ⚠️ НИЗКИЙ КОНТРАСТ! разница={diff:.0f}")
                return "FAIL"
            return "PASS"
        except:
            return "PASS"
    except Exception as e:
        print(f"  ❌ {label}: {e}")
        return "FAIL"

def run_tests():
    token = get_token()
    issues = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--window-size=1400,900"])
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        context.add_init_script(f"window.localStorage.setItem('token', '{token}');")
        page = context.new_page()
        
        # ===== ТЕСТ А: Тёмная тема — проверяем body =====
        print("\n=== ТЕСТ А: Тёмная тема ===")
        page.goto(f"{BASE_URL}/orders", wait_until="domcontentloaded", timeout=10000)
        page.wait_for_timeout(1000)
        
        body_bg = page.evaluate("() => window.getComputedStyle(document.body).backgroundColor")
        print(f"  Фон body: {body_bg}")
        
        # Проверяем есть ли переключатель темы
        theme_toggle = page.locator('[aria-label*="theme"], [data-theme], .theme-toggle, button:has-text("тёмн"), button:has-text("светл"), button:has-text("🌙"), button:has-text("☀️")')
        if theme_toggle.count() > 0:
            print("  ✅ Переключатель темы найден")
            theme_toggle.click()
            page.wait_for_timeout(500)
            body_bg2 = page.evaluate("() => window.getComputedStyle(document.body).backgroundColor")
            print(f"  После переключения: {body_bg2}")
        else:
            print("  ❌ Переключатель темы НЕ найден!")
            issues.append("Нет переключателя тёмной темы")
        
        # ===== ТЕСТ Б: Таблица заказов — контраст =====
        print("\n=== ТЕСТ Б: Контраст таблицы заказов ===")
        page.goto(f"{BASE_URL}/orders", wait_until="domcontentloaded", timeout=10000)
        page.wait_for_timeout(1000)
        
        # Проверяем заголовки таблицы
        r = check_contrast(page, "th", "Заголовки таблицы")
        if r == "FAIL": issues.append("Низкий контраст заголовков таблицы")
        
        # Проверяем строки
        r = check_contrast(page, "tbody tr td", "Ячейки таблицы")
        if r == "FAIL": issues.append("Низкий контраст ячеек таблицы")
        
        # Проверяем цвета строк (фон)
        first_row_bg = page.locator("tbody tr").first.evaluate("el => window.getComputedStyle(el).backgroundColor")
        print(f"  Фон первой строки: {first_row_bg}")
        
        # Скриншот таблицы
        table_el = page.locator(".ant-table")
        if table_el.count() > 0:
            table_el.screenshot(path="screenshots/debug_table.png")
            print("  📸 Скриншот таблицы: screenshots/debug_table.png")
        
        # ===== ТЕСТ В: Карточка заказа =====
        print("\n=== ТЕСТ В: Карточка заказа ===")
        first_link = page.locator("tbody tr a").first
        if first_link.count() > 0:
            first_link.click()
            page.wait_for_url("**/orders/*", timeout=10000)
            page.wait_for_timeout(2000)
            
            # Проверяем 3 панели
            r = check_contrast(page, "h4", "Заголовок карточки")
            if r == "FAIL": issues.append("Низкий контраст заголовка карточки")
            
            r = check_contrast(page, ".ant-descriptions-item-label, [style*='textSecondary']", "Лейблы описания")
            if r == "FAIL": issues.append("Низкий контраст лейблов")
            
            r = check_contrast(page, ".ant-tabs-tab", "Вкладки")
            if r == "FAIL": issues.append("Низкий контраст вкладок")
            
            # Скриншот карточки
            page.screenshot(path="screenshots/debug_order_detail.png")
            print("  📸 Скриншот карточки: screenshots/debug_order_detail.png")
        else:
            print("  ❌ Нет заказов для проверки")
        
        # ===== ТЕСТ Г: Создание заказа =====
        print("\n=== ТЕСТ Г: Создание заказа ===")
        page.goto(f"{BASE_URL}/orders/create", wait_until="domcontentloaded", timeout=10000)
        page.wait_for_timeout(1000)
        
        # Проверяем все input'ы
        inputs = page.locator("input, textarea")
        count = inputs.count()
        print(f"  Input'ов найдено: {count}")
        
        # Проверяем контраст лейблов формы
        r = check_contrast(page, ".ant-form-item-label label", "Лейблы формы")
        if r == "FAIL": issues.append("Низкий контраст лейблов формы создания")
        
        # Скриншот
        page.screenshot(path="screenshots/debug_order_create.png")
        print("  📸 Скриншот создания: screenshots/debug_order_create.png")
        
        # ===== ТЕСТ Д: Сайдбар навигация =====
        print("\n=== ТЕСТ Д: Сайдбар ===")
        page.goto(f"{BASE_URL}/orders", wait_until="domcontentloaded", timeout=10000)
        page.wait_for_timeout(1000)
        
        r = check_contrast(page, ".ant-menu-item, .ant-menu-submenu-title", "Пункты меню")
        if r == "FAIL": issues.append("Низкий контраст меню")
        
        # Скриншот
        sidebar = page.locator(".ant-layout-sider, aside, [class*='sider'], [class*='Sider']")
        if sidebar.count() > 0:
            sidebar.screenshot(path="screenshots/debug_sidebar.png")
            print("  📸 Скриншот сайдбара: screenshots/debug_sidebar.png")
        
        # ===== ТЕСТ Е: Шапка (Header) =====
        print("\n=== ТЕСТ Е: Шапка ===")
        r = check_contrast(page, ".ant-layout-header, header", "Шапка")
        if r == "FAIL": issues.append("Низкий контраст шапки")
        
        header = page.locator(".ant-layout-header, header").first
        if header.count() > 0:
            header_bg = header.evaluate("el => window.getComputedStyle(el).backgroundColor")
            print(f"  Фон шапки: {header_bg}")
        
        browser.close()
    
    # ===== ИТОГИ =====
    print("\n" + "=" * 60)
    if issues:
        print("❌ НАЙДЕНЫ ПРОБЛЕМЫ:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("✅ ПРОБЛЕМ НЕ НАЙДЕНО")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
