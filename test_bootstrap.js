const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    const errors = [];
    page.on('console', msg => {
        if (msg.type() === 'error') {
            errors.push(msg.text());
        }
    });
    page.on('pageerror', err => {
        errors.push('PAGE ERROR: ' + err.message);
    });
    
    await page.goto('http://localhost:20425/metadata', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    
    // 检查 Bootstrap 是否加载
    const bootstrapLoaded = await page.evaluate(() => typeof bootstrap !== 'undefined');
    console.log('Bootstrap loaded:', bootstrapLoaded);
    
    // 检查 Tab 类是否存在
    const tabClassExists = await page.evaluate(() => {
        try {
            return typeof bootstrap.Tab === 'function';
        } catch(e) {
            return false;
        }
    });
    console.log('bootstrap.Tab function exists:', tabClassExists);
    
    // 点击结果数据字段标签
    await page.click('#result-tab');
    await page.waitForTimeout(1000);
    
    // 再次检查 display
    const rawDisplay = await page.locator('#raw-fields').evaluate(el => window.getComputedStyle(el).display);
    const resultDisplay = await page.locator('#result-fields').evaluate(el => window.getComputedStyle(el).display);
    
    console.log('\n点击#result-tab后:');
    console.log('raw-fields display:', rawDisplay);
    console.log('result-fields display:', resultDisplay);
    
    console.log('\n=== 控制台错误 ===');
    if (errors.length > 0) {
        errors.forEach(e => console.log(e));
    } else {
        console.log('无错误');
    }
    
    await browser.close();
})();
