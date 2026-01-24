/**
 * BioData Manager 第3轮回归测试 - 稳定版
 */

const { chromium } = require('playwright');

(async () => {
    console.log('='.repeat(70));
    console.log('BioData Manager 第3轮回归测试');
    console.log('测试日期: 2026-01-24');
    console.log('='.repeat(70));

    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox']
    });
    
    const page = await browser.newPage();
    const testResults = { passed: 0, failed: 0, tests: [] };
    const consoleErrors = [];
    const pageErrors = [];
    
    page.on('console', msg => {
        if (msg.type() === 'error') consoleErrors.push(msg.text());
    });
    page.on('pageerror', err => pageErrors.push(err.message));
    
    function recordTest(module, name, passed, details) {
        const status = passed ? 'PASS' : 'FAIL';
        console.log(`[${status}] ${module} - ${name}`);
        if (!passed && details) console.log(`       ${details}`);
        testResults.passed += passed ? 1 : 0;
        testResults.failed += passed ? 0 : 1;
    }
    
    try {
        // ========== PRJ - 项目管理 ==========
        console.log('\n--- PRJ: 项目管理功能 ---');
        
        // PRJ-01: 新建原始数据项目按钮
        await page.goto('http://localhost:20425/raw-data', { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForTimeout(3000);
        
        const rawCreateBtn = await page.locator('button:has-text("新建原始数据项目")').count();
        recordTest('PRJ', 'PRJ-01 新建原始数据项目按钮', rawCreateBtn > 0, rawCreateBtn ? '' : '按钮未找到');
        
        // PRJ-02: 新建结果数据项目按钮
        await page.goto('http://localhost:20425/results', { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForTimeout(3000);
        
        const resCreateBtn = await page.locator('button:has-text("新建结果项目")').count();
        recordTest('PRJ', 'PRJ-02 新建结果数据项目按钮', resCreateBtn > 0, resCreateBtn ? '' : '按钮未找到');
        
        // PRJ-05: 编辑项目信息按钮
        const viewDetailBtns = await page.locator('button[onclick^="viewDetail"]').count();
        recordTest('PRJ', 'PRJ-05 查看/编辑项目按钮', viewDetailBtns > 0, viewDetailBtns ? '' : '按钮未找到');
        
        // PRJ-06: 删除项目按钮
        const deleteBtns = await page.locator('button[onclick^="deleteProject"]').count();
        recordTest('PRJ', 'PRJ-06 删除项目按钮', deleteBtns > 0, deleteBtns ? '' : '按钮未找到');
        
        // ========== FILE - 文件操作 ==========
        console.log('\n--- FILE: 文件操作功能 ---');
        await page.goto('http://localhost:20425/files', { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForTimeout(3000);
        
        const batchDelBtn = await page.locator('button:has-text("删除选中")').count();
        recordTest('FILE', 'FILE-02 批量删除按钮', batchDelBtn > 0, batchDelBtn ? '' : '按钮未找到');
        
        // ========== PAGE/SORT - 分页排序 ==========
        console.log('\n--- PAGE/SORT: 分页排序功能 ---');
        await page.goto('http://localhost:20425/raw-data', { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForTimeout(2000);
        
        const rawPagination = await page.locator('#pagination').count();
        recordTest('PAGE', 'PAGE-01 原始数据分页控件', rawPagination > 0, rawPagination ? '' : '控件未找到');
        
        await page.goto('http://localhost:20425/results', { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForTimeout(2000);
        
        const resPagination = await page.locator('#pagination').count();
        recordTest('PAGE', 'PAGE-02 结果数据分页控件', resPagination > 0, resPagination ? '' : '控件未找到');
        
        // ========== SFIL - 筛选功能 ==========
        console.log('\n--- SFIL: 筛选功能 ---');
        await page.goto('http://localhost:20425/raw-data', { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForTimeout(2000);
        
        const rawFilterType = await page.locator('#filter-raw_type option').count();
        recordTest('SFIL', 'SFIL-01 原始数据筛选选项', rawFilterType > 1, `选项数: ${rawFilterType}`);
        
        const resetBtn = await page.locator('button:has-text("重置")').count();
        recordTest('SFIL', 'SFIL-03 重置按钮', resetBtn > 0, resetBtn ? '' : '按钮未找到');
        
        await page.goto('http://localhost:20425/results', { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForTimeout(2000);
        
        const resFilterType = await page.locator('#filter-results_type option').count();
        recordTest('SFIL', 'SFIL-02 结果数据筛选选项', resFilterType > 1, `选项数: ${resFilterType}`);
        
        // ========== MDET - 详情弹窗 ==========
        console.log('\n--- MDET: 详情弹窗 ---');
        await page.goto('http://localhost:20425/raw-data', { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForTimeout(2000);
        
        if (await page.locator('button[onclick^="viewDetail"]').count() > 0) {
            await page.locator('button[onclick^="viewDetail"]').first().click();
            await page.waitForTimeout(3000);
            
            const modalContent = await page.locator('#detail-modal .modal-content').count();
            recordTest('MDET', 'MDET-01 原始数据详情弹窗', modalContent > 0, modalContent ? '' : '弹窗未打开');
            
            await page.click('#detail-modal .btn-close').catch(() => {});
            await page.waitForTimeout(2000);
        }
        
        await page.goto('http://localhost:20425/results', { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForTimeout(2000);
        
        if (await page.locator('button[onclick^="viewDetail"]').count() > 0) {
            await page.locator('button[onclick^="viewDetail"]').first().click();
            await page.waitForTimeout(3000);
            
            const modalContent = await page.locator('#detail-modal .modal-content').count();
            recordTest('MDET', 'MDET-02 结果数据详情弹窗', modalContent > 0, modalContent ? '' : '弹窗未打开');
        }
        
        // ========== CIT - 引文解析 ==========
        console.log('\n--- CIT: 引文解析功能 ---');
        await page.goto('http://localhost:20425/raw-data', { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForTimeout(2000);
        
        const citationBtn = await page.locator('button:has-text("引文文件")').count();
        recordTest('CIT', 'CIT-01 引文文件按钮', citationBtn > 0, citationBtn ? '' : '按钮未找到');
        
        // ========== META - 元数据配置 ==========
        console.log('\n--- META: 元数据配置 ---');
        await page.goto('http://localhost:20425/metadata', { waitUntil: 'networkidle', timeout: 30000 });
        await page.waitForTimeout(3000);
        
        const rawTab = await page.locator('#raw-tab').count();
        const resTab = await page.locator('#result-tab').count();
        recordTest('META', 'META-01 原始数据标签页', rawTab > 0, rawTab ? '' : '标签页未找到');
        recordTest('META', 'META-01 结果数据标签页', resTab > 0, resTab ? '' : '标签页未找到');
        
        // 等待字段列表加载
        await page.waitForTimeout(2000);
        
        const rawFieldRows = await page.locator('#raw-field-list tr').count();
        const resFieldRows = await page.locator('#result-field-list tr').count();
        recordTest('META', 'META-01 原始数据字段列表', rawFieldRows > 0, `行数: ${rawFieldRows}`);
        recordTest('META', 'META-01 结果数据字段列表', resFieldRows > 0, `行数: ${resFieldRows}`);
        
    } catch (err) {
        console.error('测试错误:', err.message);
        testResults.failed++;
    } finally {
        await browser.close();
    }
    
    // 结果汇总
    console.log('\n' + '='.repeat(70));
    console.log('第3轮测试结果汇总');
    console.log('='.repeat(70));
    console.log(`总测试数: ${testResults.passed + testResults.failed}`);
    console.log(`通过: ${testResults.passed}`);
    console.log(`失败: ${testResults.failed}`);
    console.log(`通过率: ${((testResults.passed / (testResults.passed + testResults.failed)) * 100).toFixed(1)}%`);
    
    if (consoleErrors.length > 0) {
        console.log(`\n控制台错误数: ${consoleErrors.length}`);
    }
    if (pageErrors.length > 0) {
        console.log(`页面错误数: ${pageErrors.length}`);
    }
    
    console.log('\n' + '='.repeat(70));
    process.exit(testResults.failed > 0 ? 1 : 0);
})();
