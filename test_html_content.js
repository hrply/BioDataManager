const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    await page.goto('http://localhost:20425/metadata', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    
    // 获取原始数据字段表格内容
    const rawTable = await page.locator('#raw-field-list').innerText();
    console.log('=== 原始数据字段表格内容 ===');
    console.log(rawTable.substring(0, 500) + '...');
    
    // 点击结果数据字段标签
    await page.click('#result-tab');
    await page.waitForTimeout(1000);
    
    // 获取结果数据字段表格内容
    const resultTable = await page.locator('#result-field-list').innerText();
    console.log('\n=== 结果数据字段表格内容 ===');
    console.log(resultTable.substring(0, 500) + '...');
    
    // 点击文件管理字段标签
    await page.click('#file-tab');
    await page.waitForTimeout(1000);
    
    // 获取文件管理字段表格内容
    const fileTable = await page.locator('#file-field-list').innerText();
    console.log('\n=== 文件管理字段表格内容 ===');
    console.log(fileTable.substring(0, 500) + '...');
    
    await browser.close();
})();
