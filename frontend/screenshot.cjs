const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

  await page.goto('http://127.0.0.1:4173/login');
  await page.waitForTimeout(500);
  await page.screenshot({ path: 'C:/Users/qpkzz/Desktop/1/work/reputa/screenshots/login.png', fullPage: true });

  await page.goto('http://127.0.0.1:4173/registration');
  await page.waitForTimeout(500);
  await page.screenshot({ path: 'C:/Users/qpkzz/Desktop/1/work/reputa/screenshots/registration.png', fullPage: true });

  await browser.close();
  console.log('done');
})();
