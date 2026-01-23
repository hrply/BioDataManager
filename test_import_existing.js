/**
 * 测试导入至已有项目功能 - 使用正确的按钮选择器
 */

const { chromium } = require('playwright');

(async () => {
    console.log('=== 测试导入至已有项目功能 ===\n');
    
    const browser = await chromium.launch();
    const page = await browser.newPage();
    
    const consoleMessages = [];
    const errors = [];
    
    page.on('console', msg => {
        const text = msg.text();
        consoleMessages.push({ type: msg.type(), text });
        if (msg.type() === 'error') {
            errors.push(text);
        }
        console.log(`[CONSOLE ${msg.type()}] ${text.substring(0, 150)}`);
    });
    
    page.on('pageerror', err => {
        errors.push('PAGE ERROR: ' + err.message);
        console.log('[PAGE ERROR]', err.message);
    });
    
    try {
        // 1. 访问文件管理页面
        console.log('1. 访问文件管理页面...');
        await page.goto('http://localhost:20425/files');
        await page.waitForTimeout(2000);
        
        // 2. 切换到导入标签页
        console.log('2. 切换到导入标签页...');
        await page.click('#import-tab');
        await page.waitForTimeout(1000);
        
        // 3. 点击扫描按钮
        console.log('3. 点击扫描按钮...');
        await page.click('#import-content button[onclick="scanDownloads()"]');
        await page.waitForTimeout(3000);
        
        // 4. 检查扫描结果
        const folderCount = await page.$$eval('#folder-list .list-group-item', items => items.length);
        console.log(`4. 找到 ${folderCount} 个文件夹`);
        
        if (folderCount > 0) {
            // 5. 点击最后一个文件夹的导入按钮
            const importBtns = await page.$$('#folder-list button[onclick^="openImportModal"]');
            console.log(`5. 找到 ${importBtns.length} 个导入按钮`);
            
            // 点击最后一个（test_import，有7个文件）
            const targetIndex = importBtns.length - 1;
            console.log(`6. 点击第 ${targetIndex + 1} 个文件夹的导入按钮...`);
            await importBtns[targetIndex].click();
            await page.waitForTimeout(1000);
            
            // 7. 选择"导入至已有项目"
            console.log('7. 选择"导入至已有项目"...');
            await page.click('label[for="mode-existing"]');
            await page.waitForTimeout(1500);
            
            // 8. 检查项目列表
            const projectOptions = await page.$$eval('#target-project option', opts => opts.map(o => ({ value: o.value, text: o.textContent.trim() })));
            console.log(`8. 项目选项: ${JSON.stringify(projectOptions)}`);
            
            if (projectOptions.length > 1) {
                // 9. 选择第一个实际项目
                await page.selectOption('#target-project', { index: 1 });
                await page.waitForTimeout(500);
                
                // 10. 检查文件选择区域
                const fileCheckboxes = await page.$$('#file-selection-area input[type="checkbox"]');
                console.log(`10. 找到 ${fileCheckboxes.length} 个文件复选框`);
                
                if (fileCheckboxes.length > 0) {
                    // 11. 选择第一个文件
                    await fileCheckboxes[0].click();
                    await page.waitForTimeout(200);
                    console.log('11. 已选择第一个文件');
                    
                    // 12. 点击确认导入 - 使用正确选择器
                    console.log('12. 点击确认导入按钮...');
                    await page.click('#import-modal .modal-footer .btn-primary');
                    await page.waitForTimeout(5000);
                }
            }
        }
        
        // 检查导入结果
        const importSuccess = consoleMessages.some(m => m.text.includes('导入成功'));
        const importFailed = consoleMessages.some(m => m.text.includes('导入失败'));
        
        console.log('\n=== 测试结果 ===');
        console.log('导入成功:', importSuccess);
        console.log('导入失败:', importFailed);
        
        if (errors.length > 0) {
            console.log('\n=== 错误 ===');
            errors.forEach(e => console.log(e));
        }
        
    } catch (err) {
        console.error('测试失败:', err.message);
    } finally {
        await browser.close();
    }
    
    console.log('\n=== 测试完成 ===');
})();
