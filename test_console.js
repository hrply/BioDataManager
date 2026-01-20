const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    const context = await browser.newContext();
    const page = await context.newPage();

    const jsErrors = [];
    const failedRequests = [];

    page.on('console', msg => {
        if (msg.type() === 'error' && !msg.text().includes('Failed to load resource')) {
            jsErrors.push(msg.text());
        }
    });

    page.on('pageerror', err => {
        jsErrors.push(`PageError: ${err.message}`);
    });

    page.on('requestfailed', request => {
        failedRequests.push({
            url: request.url(),
            failure: request.failure()?.errorText
        });
    });

    try {
        console.log('快速点击测试...');
        await page.goto('http://192.168.3.147:20425/results', {
            waitUntil: 'domcontentloaded',
            timeout: 30000
        });

        // 快速点击刷新按钮 10 次
        for (let i = 0; i < 10; i++) {
            await page.keyboard.press('F5');
            await page.waitForTimeout(200);
        }

        console.log('\n=== 快速点击测试结果 ===');
        console.log('页面标题:', await page.title());

        if (jsErrors.length > 0) {
            console.log(`\n❌ JavaScript 错误: ${jsErrors.length}`);
            jsErrors.forEach((err, i) => console.log(`  ${i + 1}. ${err.substring(0, 100)}`));
        } else {
            console.log('\n✅ 无 JavaScript 错误');
        }

        if (failedRequests.length > 0) {
            console.log(`\n⚠️ 网络请求失败: ${failedRequests.length}`);
            failedRequests.forEach((req, i) => {
                console.log(`  ${i + 1}. ${req.url.substring(0, 60)}`);
            });
        } else {
            console.log('✅ 所有请求成功');
        }

    } catch (e) {
        console.error('\n❌ 测试失败:', e.message);
    } finally {
        await browser.close();
    }

    process.exit(jsErrors.length > 0 ? 1 : 0);
})();