const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    await page.goto('http://localhost:20425/metadata', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    
    // 获取原始数据字段的HTML
    const rawHTML = await page.locator('#raw-field-list').innerHTML();
    console.log('=== 原始数据字段HTML ===');
    console.log(rawHTML.substring(0, 800));
    
    // 点击结果数据字段标签
    await page.click('#result-tab');
    await page.waitForTimeout(1000);
    
    // 获取结果数据字段的HTML
    const resultHTML = await page.locator('#result-field-list').innerHTML();
    console.log('\n=== 结果数据字段HTML ===');
    console.log(resultHTML.substring(0, 800));
    
    await browser.close();
})();
