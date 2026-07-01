"""
Визуальный тест — делает скриншоты в светлой и тёмной теме, проверяет контраст
"""
import json
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:5173"

def get_token():
    import urllib.request
    req = urllib.request.Request("http://localhost:8000/api/auth/login",
        data=json.dumps({"username": "admin", "password": "admin"}).encode(),
        headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())["access_token"]

def check_pixel_contrast(page, label):
    """Проверяем средний контраст на скриншоте"""
    page.screenshot(path=f"screenshots/{label}.png", full_page=True)
    
    # Получаем пиксели из центра экрана
    pixels = page.evaluate("""() => {
        const canvas = document.createElement('canvas');
        canvas.width = 200;
        canvas.height = 200;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(document.body, 0, 0, 200, 200);
        const data = ctx.getImageData(0, 0, 200, 200).data;
        let white = 0, dark = 0, total = data.length / 4;
        for (let i = 0; i < data.length; i += 4) {
            const brightness = (data[i] + data[i+1] + data[i+2]) / 3;
            if (brightness > 240) white++;
            else if (brightness < 40) dark++;
        }
        return { white: (white/total*100).toFixed(1), dark: (dark/total*100).toFixed(1), total };
    }""")
    return pixels

def run_tests():
    token = get_token()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--window-size=1400,900"])
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            ignore_https_errors=True,
        )
        context.add_init_script(f"""
            window.localStorage.setItem('token', '{token}');
            window.localStorage.setItem('theme', 'light');
        """)
        # Отключаем кэш
        context.add_init_script("window.caches && caches.keys().then(k => k.forEach(c => caches.delete(c)));")
        page = context.new_page()
        page.route("**/*", lambda route: route.continue_())
        
        print("\n=== СВЕТЛАЯ ТЕМА ===")
        page.goto(f"{BASE_URL}/orders", wait_until="domcontentloaded", timeout=10000)
        page.wait_for_timeout(1500)
        
        # Фон body
        body_bg = page.evaluate("() => window.getComputedStyle(document.documentElement).backgroundColor")
        print(f"  Фон: {body_bg}")
        
        # Шапка
        header_bg = page.evaluate("""() => {
            const h = document.querySelector('.ant-layout-header');
            return h ? window.getComputedStyle(h).backgroundColor : 'not found';
        }""")
        print(f"  Фон шапки: {header_bg}")
        
        # Текст в шапке
        header_text_color = page.evaluate("""() => {
            const span = document.querySelector('.ant-layout-header span');
            return span ? window.getComputedStyle(span).color : 'not found';
        }""")
        print(f"  Цвет текста в шапке: {header_text_color}")
        
        # Переключатель темы — ищем Switch
        switch_el = page.evaluate("""() => {
            const btn = document.querySelector('.ant-switch');
            return btn ? {
                bg: window.getComputedStyle(btn).backgroundColor,
                exists: true
            } : { exists: false };
        }""")
        print(f"  Переключатель: {'найден' if switch_el.get('exists') else 'НЕ НАЙДЕН'}")
        
        # Открываем карточку заказа
        first_link = page.locator("tbody tr a").first
        if first_link.count() > 0:
            first_link.click()
            page.wait_for_url("**/orders/*", timeout=10000)
            page.wait_for_timeout(2000)
            
            # Заголовок карточки
            h4_color = page.evaluate("""() => {
                const h = document.querySelector('h4');
                return h ? window.getComputedStyle(h).color : 'not found';
            }""")
            h4_bg = page.evaluate("""() => {
                const h = document.querySelector('h4');
                if (!h) return 'not found';
                let el = h;
                while (el) {
                    const bg = window.getComputedStyle(el).backgroundColor;
                    if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') return bg;
                    el = el.parentElement;
                }
                return 'transparent';
            }""")
            print(f"\n  Карточка заказа:")
            print(f"    Заголовок h4: цвет={h4_color}, фон={h4_bg}")
            
            page.screenshot(path="screenshots/order_detail_light.png", full_page=True)
            print(f"  📸 screenshots/order_detail_light.png")
        
        # ===== ТЁМНАЯ ТЕМА =====
        print("\n=== ТЁМНАЯ ТЕМА ===")
        page.goto(f"{BASE_URL}/orders", wait_until="domcontentloaded", timeout=10000)
        page.wait_for_timeout(500)
        
        # Кликаем переключатель
        switch = page.locator('.ant-switch').first
        if switch.count() > 0:
            switch.click()
            page.wait_for_timeout(1000)
            print("  ✅ Переключатель кликабельный")
        else:
            print("  ❌ Переключатель НЕ найден!")
        
        # Фон
        body_bg_dark = page.evaluate("() => window.getComputedStyle(document.documentElement).backgroundColor")
        print(f"  Фон: {body_bg_dark}")
        
        # Шапка тёмная
        header_bg_dark = page.evaluate("""() => {
            const h = document.querySelector('.ant-layout-header');
            return h ? window.getComputedStyle(h).backgroundColor : 'not found';
        }""")
        print(f"  Фон шапки: {header_bg_dark}")
        
        header_text_dark = page.evaluate("""() => {
            const span = document.querySelector('.ant-layout-header span');
            return span ? window.getComputedStyle(span).color : 'not found';
        }""")
        print(f"  Цвет текста в шапке: {header_text_dark}")
        
        # Карточка в тёмной теме
        first_link2 = page.locator("tbody tr a").first
        if first_link2.count() > 0:
            first_link2.click()
            page.wait_for_url("**/orders/*", timeout=10000)
            page.wait_for_timeout(2000)
            
            h4_color_dark = page.evaluate("""() => {
                const h = document.querySelector('h4');
                return h ? window.getComputedStyle(h).color : 'not found';
            }""")
            h4_bg_dark = page.evaluate("""() => {
                const h = document.querySelector('h4');
                if (!h) return 'not found';
                let el = h;
                while (el) {
                    const bg = window.getComputedStyle(el).backgroundColor;
                    if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') return bg;
                    el = el.parentElement;
                }
                return 'transparent';
            }""")
            print(f"\n  Карточка заказа (тёмная):")
            print(f"    Заголовок h4: цвет={h4_color_dark}, фон={h4_bg_dark}")
            
            # Проверка контраста
            def brightness(s):
                try:
                    nums = [int(x) for x in s.replace('rgb(','').replace('rgba(','').replace(')','').split(',')[:3]]
                    return sum(nums) / 3
                except:
                    return -1
            
            tc = brightness(h4_color_dark)
            tbg = brightness(h4_bg_dark)
            diff = abs(tc - tbg)
            print(f"    Контраст: {diff:.0f} {'✅ OK' if diff > 50 else '❌ НИЗКИЙ!'}")
            
            page.screenshot(path="screenshots/order_detail_dark.png", full_page=True)
            print(f"  📸 screenshots/order_detail_dark.png")
        
        # Общий скриншот тёмной темы
        page.goto(f"{BASE_URL}/orders", wait_until="domcontentloaded", timeout=10000)
        page.wait_for_timeout(1000)
        page.screenshot(path="screenshots/overview_dark.png", full_page=True)
        print(f"\n  📸 screenshots/overview_dark.png")
        
        # Анализ пикселей
        pixels = check_pixel_contrast(page, "pixel_analysis_dark")
        print(f"\n  Пиксели: белых={pixels['white']}%, тёмных={pixels['dark']}%")
        
        browser.close()
        
        print("\n" + "=" * 60)
        print("Готово! Скриншоты в screenshots/")
        print("=" * 60)

if __name__ == "__main__":
    run_tests()
