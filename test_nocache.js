const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch();
    const context = await browser.newContext({
        bypassCSP: true
    });
    const page = await context.newPage();
    
    // 强制禁用缓存
    await page.route('**', route => {
        route.continue({
            headers: {
                ...route.request().headers(),
                'Cache-Control': 'no-cache, no-store, must-revalidate'
            }
        });
    });
    
    await page.goto('http://localhost:20425/metadata', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    
    console.log('=== 禁用缓存后的 DOM 结构 ===');
    const children = await page.evaluate(() => {
        const container = document.getElementById('metadata-tab-content');
        return Array.from(container.children).map((child, i) => ({
            index: i,
            tag: child.tagName,
            id: child.id,
            class: child.className
        }));
    });
    
    console.log('直接子元素数量:', children.length);
    children.forEach(c => {
        console.log(`  [${c.index}] <${c.tag}> id="${c.id}" class="${c.class}"`);
    });
    
    // 查找所有 tab-pane
    console.log('\n=== 页面中所有的 tab-pane ===');
    const allPanes = await page.evaluate(() => {
        return Array.from(document.querySelectorAll('.tab-pane')).map(el => ({
            id: el.id,
            parentId: el.parentElement.id,
            class: el.className
        }));
    });
    allPanes.forEach(p => {
        console.log(`id="${p.id}" parent="#${p.parentId}" class="${p.class}"`);
    });
    
    await browser.close();
})();
