const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    // 监听网络请求和响应
    page.on('response', async response => {
        if (response.url().includes('/metadata') && response.status() === 200) {
            const text = await response.text();
            console.log('=== 服务器返回的HTML中的tab-content结构 ===');
            
            // 用正则提取 tab-content 内部的所有 div
            const match = text.match(/<div class="tab-content" id="metadata-tab-content">([\s\S]*?)<\/div>\s*<\/div>/);
            if (match) {
                const content = match[1];
                const divCount = (content.match(/<div class="tab-pane/g) || []).length;
                console.log('tab-content 内发现 tab-pane 数量:', divCount);
                
                // 列出所有 tab-pane 的 id
                const ids = content.match(/id="(result-fields|file-fields|abbr-mapping|raw-fields)"/g);
                if (ids) {
                    console.log('发现的 tab-pane IDs:', ids.join(', '));
                }
            }
        }
    });
    
    await page.goto('http://localhost:20425/metadata', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(5000);
    
    console.log('\n=== 浏览器渲染后的 DOM 结构 ===');
    
    // 检查 tab-content 的直接子元素
    const directChildren = await page.evaluate(() => {
        const container = document.getElementById('metadata-tab-content');
        if (!container) return { error: 'container not found' };
        
        return {
            childCount: container.children.length,
            children: Array.from(container.children).map((child, i) => ({
                index: i,
                tag: child.tagName,
                id: child.id,
                class: child.className
            }))
        };
    });
    
    console.log('直接子元素数量:', directChildren.childCount);
    directChildren.children.forEach(c => {
        console.log(`  [${c.index}] <${c.tag}> id="${c.id}" class="${c.class}"`);
    });
    
    // 完整嵌套检查
    console.log('\n=== 完整 HTML 结构 ===');
    const fullHtml = await page.evaluate(() => {
        return document.getElementById('metadata-tab-content').outerHTML;
    });
    console.log(fullHtml.substring(0, 2000));
    
    await browser.close();
})();
