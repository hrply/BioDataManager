const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    await page.goto('http://localhost:20425/metadata', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(3000);
    
    // 检查 tab-content 的直接子元素
    console.log('=== 检查 #metadata-tab-content 的直接子元素 ===');
    const children = await page.evaluate(() => {
        const container = document.getElementById('metadata-tab-content');
        const childElements = Array.from(container.children);
        return childElements.map(el => ({
            tag: el.tagName,
            id: el.id,
            class: el.className
        }));
    });
    children.forEach((c, i) => {
        console.log(`${i + 1}. <${c.tag}> id="${c.id}" class="${c.class}"`);
    });
    
    // 检查 raw-fields 里面有什么
    console.log('\n=== 检查 #raw-fields 的直接子元素 ===');
    const rawChildren = await page.evaluate(() => {
        const el = document.getElementById('raw-fields');
        return Array.from(el.children).map(child => ({
            tag: child.tagName,
            id: child.id || '无',
            class: child.className || '无'
        }));
    });
    rawChildren.forEach((c, i) => {
        console.log(`${i + 1}. <${c.tag}> id="${c.id}" class="${c.class}"`);
    });
    
    // 检查是否有嵌套的 tab-pane
    console.log('\n=== 检查是否有嵌套的 tab-pane ===');
    const nestedPanes = await page.evaluate(() => {
        const rawFields = document.getElementById('raw-fields');
        const nested = rawFields.querySelectorAll('.tab-pane');
        return Array.from(nested).map(el => el.id);
    });
    console.log('raw-fields 内的 tab-pane:', nestedPanes.length > 0 ? nestedPanes.join(', ') : '无');
    
    await browser.close();
})();
