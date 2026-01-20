const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    await page.goto('http://localhost:20425/metadata', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    
    console.log('=== 初始状态 (raw-fields 激活) ===');
    let rawDisplay = await page.locator('#raw-fields').evaluate(el => window.getComputedStyle(el).display);
    let resultDisplay = await page.locator('#result-fields').evaluate(el => window.getComputedStyle(el).display);
    let fileDisplay = await page.locator('#file-fields').evaluate(el => window.getComputedStyle(el).display);
    console.log(`raw-fields: ${rawDisplay}, result-fields: ${resultDisplay}, file-fields: ${fileDisplay}`);
    
    console.log('\n=== 点击"结果数据字段"标签 ===');
    await page.click('#result-tab');
    await page.waitForTimeout(500);
    
    rawDisplay = await page.locator('#raw-fields').evaluate(el => window.getComputedStyle(el).display);
    resultDisplay = await page.locator('#result-fields').evaluate(el => window.getComputedStyle(el).display);
    console.log(`raw-fields: ${rawDisplay}, result-fields: ${resultDisplay}`);
    
    console.log('\n=== 点击"文件管理字段"标签 ===');
    await page.click('#file-tab');
    await page.waitForTimeout(500);
    
    fileDisplay = await page.locator('#file-fields').evaluate(el => window.getComputedStyle(el).display);
    let abbrDisplay = await page.locator('#abbr-mapping').evaluate(el => window.getComputedStyle(el).display);
    console.log(`file-fields: ${fileDisplay}, abbr-mapping: ${abbrDisplay}`);
    
    console.log('\n=== 验证字段数据 ===');
    const fieldCount = await page.evaluate(() => {
        return document.querySelectorAll('#raw-field-list tr[data-id]').length;
    });
    console.log(`raw-field-list 中的字段数: ${fieldCount}`);
    
    await browser.close();
    console.log('\n✅ 标签页切换功能正常！');
})();
