const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    await page.goto('http://localhost:20425/metadata', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    
    // 点击"结果数据字段"标签
    await page.click('#result-tab');
    await page.waitForTimeout(1000);
    
    // 获取标签页内容
    const rawContent = await page.locator('#raw-fields').innerHTML();
    const resultContent = await page.locator('#result-fields').innerHTML();
    
    console.log('=== 原始数据字段标签页内容长度:', rawContent.length);
    console.log('=== 结果数据字段标签页内容长度:', resultContent.length);
    
    // 检查是否包含渲染的行
    const rawRows = await page.locator('#raw-field-list tr').count();
    const resultRows = await page.locator('#result-field-list tr').count();
    const fileRows = await page.locator('#file-field-list tr').count();
    
    console.log('\n=== 各标签页行数 ===');
    console.log('原始数据字段行数:', rawRows);
    console.log('结果数据字段行数:', resultRows);
    console.log('文件管理字段行数:', fileRows);
    
    // 检查是否有"加载中"文本
    const rawLoading = await page.locator('#raw-field-list:has-text("加载中")').count();
    const resultLoading = await page.locator('#result-field-list:has-text("加载中")').count();
    console.log('\n=== 加载状态 ===');
    console.log('原始数据字段仍在加载:', rawLoading > 0);
    console.log('结果数据字段仍在加载:', resultLoading > 0);
    
    await browser.close();
})();
