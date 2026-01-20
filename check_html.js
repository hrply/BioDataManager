const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    await page.goto('http://localhost:20425/metadata', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    
    // 获取完整的 tab-content HTML
    const html = await page.locator('#metadata-tab-content').innerHTML();
    
    // 统计 div 开始和结束标签
    const openDivs = (html.match(/<div/g) || []).length;
    const closeDivs = (html.match(/<\/div>/g) || []).length;
    
    console.log('=== HTML 结构检查 ===');
    console.log('<div> 标签数量:', openDivs);
    console.log('</div> 标签数量:', closeDivs);
    console.log('差异:', openDivs - closeDivs);
    
    // 检查 tab-pane 的 display 样式
    console.log('\n=== 各标签页 display 样式 ===');
    const tabPanes = ['raw-fields', 'result-fields', 'file-fields', 'abbr-mapping'];
    for (const id of tabPanes) {
        const display = await page.locator('#' + id).evaluate(el => window.getComputedStyle(el).display);
        console.log(id + ': display =', display);
    }
    
    await browser.close();
})();
