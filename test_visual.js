const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    // 设置更大的视口
    await page.setViewportSize({ width: 1920, height: 1080 });
    
    await page.goto('http://localhost:20425/metadata', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    
    // 点击各个标签页并截图
    await page.screenshot({ path: '/tmp/metadata_raw.png', fullPage: true });
    console.log('已保存截图: metadata_raw.png (原始数据字段标签页)');
    
    // 点击结果数据字段
    await page.click('#result-tab');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: '/tmp/metadata_result.png', fullPage: true });
    console.log('已保存截图: metadata_result.png (结果数据字段标签页)');
    
    // 点击文件管理字段
    await page.click('#file-tab');
    await page.waitForTimeout(1000);
    await page.screenshot({ path: '/tmp/metadata_file.png', fullPage: true });
    console.log('已保存截图: metadata_file.png (文件管理字段标签页)');
    
    await browser.close();
})();
