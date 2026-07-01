const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  const errors = [];
  page.on('pageerror', err => {
    errors.push(err.message);
    console.error('❌ JS Error:', err.message.substring(0, 200));
  });
  page.on('response', response => {
    if (response.status() >= 400 && !response.url().includes('vite')) {
      console.error(`❌ HTTP ${response.status()}: ${response.url().substring(0, 80)}`);
    }
  });

  const testPage = async (name, url) => {
    console.log(`\n📄 ${name}`);
    try {
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 10000 });
      await page.waitForTimeout(2000);
      
      const title = await page.title();
      console.log(`   Title: "${title}"`);
      console.log(`   URL: ${page.url()}`);
      
      const bodyText = await page.textContent('body');
      if (bodyText && bodyText.includes('Внутренняя ошибка')) {
        console.log('   ❌ Ошибка сервера');
      } else if (bodyText && bodyText.includes('File not found')) {
        console.log('   ❌ 404 Not Found');
      } else {
        console.log('   ✅ Страница загружена');
      }
      
      await page.screenshot({ path: `/tmp/screen-${name.replace(/[^a-zA-Z]/g, '')}.png`, fullPage: false });
      return true;
    } catch (e) {
      console.log(`   ❌ Ошибка: ${e.message.substring(0, 100)}`);
      return false;
    }
  };

  // 1. Логин
  await testPage('Login', 'http://127.0.0.1:5173/');
  await page.waitForTimeout(1000);
  
  // Логин
  try {
    await page.fill('input[placeholder="Имя пользователя"]', 'admin');
    await page.fill('input[type="password"]', 'admin');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(3000);
    console.log('   ✅ Логин выполнен');
  } catch (e) {
    console.log(`   ⚠️ Логин: ${e.message.substring(0, 80)}`);
  }

  // 2. Дашборд
  await testPage('Dashboard', 'http://127.0.0.1:5173/dashboard');
  
  // 3. Заказы
  await testPage('Orders', 'http://127.0.0.1:5173/orders');
  
  // 4. Создание заказа
  await testPage('CreateOrder', 'http://127.0.0.1:5173/orders/create');
  
  // 5. Настройки
  await testPage('Settings', 'http://127.0.0.1:5173/settings');
  
  // 6. Профиль
  await testPage('Profile', 'http://127.0.0.1:5173/profile');

  // Итог
  console.log('\n' + '='.repeat(50));
  console.log('📊 РЕЗУЛЬТАТ:');
  console.log(`   Страниц проверено: 6`);
  console.log(`   JS ошибок: ${errors.length}`);
  if (errors.length > 0) {
    errors.forEach((e, i) => console.log(`   ${i+1}. ${e.substring(0, 150)}`));
  }
  console.log('   Скриншоты: /tmp/screen-*.png');

  await browser.close();
})();
