const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    const consoleErrors = [];
    page.on('console', msg => {
        if (msg.type() === 'error') {
            consoleErrors.push(`ERROR: ${msg.text()}`);
        }
    });
    
    const pageErrors = [];
    page.on('pageerror', err => {
        pageErrors.push(err.message);
    });
    
    try {
        await page.goto('http://localhost:20425/metadata', { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForTimeout(3000);
        
        const rawCount = await page.locator('#raw-field-list tr').count();
        const resultCount = await page.locator('#result-field-list tr').count();
        const fileCount = await page.locator('#file-field-list tr').count();
        
        console.log('=== 页面渲染结果 ===');
        console.log(`原始数据字段行数: ${rawCount}`);
        console.log(`结果数据字段行数: ${resultCount}`);
        console.log(`文件管理字段行数: ${fileCount}`);
        
        console.log('\n=== 控制台错误 ===');
        if (consoleErrors.length > 0) {
            consoleErrors.forEach(msg => console.log(msg));
        } else {
            console.log('无控制台错误');
        }
        
        console.log('\n=== 页面错误 ===');
        if (pageErrors.length > 0) {
            pageErrors.forEach(err => console.log(err));
        } else {
            console.log('无页面错误');
        }
        
    } catch (err) {
        console.log('页面加载错误:', err.message);
    }
    
    await browser.close();
})();
