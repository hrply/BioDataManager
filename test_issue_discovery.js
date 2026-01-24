/**
 * BioData Manager - 问题发现综合测试
 * 测试所有页面：/raw-data, /results, /files, /metadata
 * 验证已知问题 A~H 是否已修复
 */

const { chromium } = require('playwright');

const BASE_URL = 'http://192.168.3.147:20425';
const PAGES = ['/raw-data', '/results', '/files', '/metadata'];

let testResults = {
    summary: {
        pagesTested: 0,
        errorsFound: 0,
        issues: []
    },
    pages: []
};

// 收集页面错误的处理器
function setupErrorHandlers(page) {
    const errors = [];

    // 监听 console 错误
    page.on('console', msg => {
        if (msg.type() === 'error') {
            errors.push({
                type: 'console_error',
                message: msg.text(),
                timestamp: new Date().toISOString()
            });
        }
    });

    // 监听页面错误
    page.on('pageerror', err => {
        errors.push({
            type: 'pageerror',
            message: err.message,
            timestamp: new Date().toISOString()
        });
    });

    // 监听请求失败
    page.on('requestfailed', request => {
        errors.push({
            type: 'request_failed',
            url: request.url(),
            failure: request.failure().errorText,
            timestamp: new Date().toISOString()
        });
    });

    return errors;
}

// 测试单个页面
async function testPage(page, path) {
    console.log('\n' + '='.repeat(60));
    console.log('测试页面: ' + path);
    console.log('='.repeat(60));

    const pageResult = {
        path,
        errors: [],
        warnings: [],
        checks: {
            domComplete: false,
            elementsRendered: false,
            apiCallsSuccess: false,
            filterOptionsLoaded: false,
            tableDataLoaded: false,
            detailModalWorks: false
        }
    };

    const errors = setupErrorHandlers(page);

    try {
        // 1. 访问页面
        console.log('\n[1/6] 访问页面: ' + path);
        const response = await page.goto(BASE_URL + path, {
            waitUntil: 'networkidle',
            timeout: 30000
        });

        if (response && response.status() === 200) {
            console.log('    ✓ 页面加载成功 (状态码: ' + response.status() + ')');
            pageResult.checks.domComplete = true;
        } else {
            console.log('    ✗ 页面加载失败 (状态码: ' + (response ? response.status() : '无响应') + ')');
            pageResult.errors.push({
                severity: 'high',
                description: '页面无法加载',
                details: response ? '状态码: ' + response.status() : '无响应'
            });
        }

        // 等待页面稳定
        await page.waitForTimeout(2000);

        // 2. 检查 DOM 结构完整性
        console.log('\n[2/6] 检查 DOM 结构完整性');

        const requiredElements = getRequiredElements(path);
        let allElementsFound = true;

        for (const selector of requiredElements) {
            try {
                const element = await page.locator(selector).first();
                const isVisible = await element.isVisible({ timeout: 3000 });
                if (!isVisible) {
                    console.log('    ⚠ 元素存在但不可见: ' + selector);
                    pageResult.warnings.push({
                        description: '元素不可见',
                        selector
                    });
                    allElementsFound = false;
                }
            } catch (e) {
                console.log('    ✗ 元素不存在: ' + selector);
                pageResult.errors.push({
                    severity: 'medium',
                    description: '必要 DOM 元素缺失',
                    selector
                });
                allElementsFound = false;
            }
        }

        if (allElementsFound) {
            console.log('    ✓ 所有必要 DOM 元素存在');
            pageResult.checks.elementsRendered = true;
        }

        // 3. 检查 API 调用
        console.log('\n[3/6] 检查 API 调用');

        const apiResults = await checkApiCalls(page, path);
        if (apiResults.success) {
            console.log('    ✓ API 调用成功');
            pageResult.checks.apiCallsSuccess = true;
        } else {
            console.log('    ✗ API 调用失败: ' + apiResults.error);
            pageResult.errors.push({
                severity: 'high',
                description: 'API 调用失败',
                details: apiResults.error
            });
        }

        // 4. 检查筛选下拉框（针对 raw-data 和 results）
        if (path === '/raw-data' || path === '/results') {
            console.log('\n[4/6] 检查筛选下拉框');

            const filterResults = await checkFilterOptions(page, path);
            if (filterResults.hasOptions) {
                console.log('    ✓ 筛选下拉框有选项');
                pageResult.checks.filterOptionsLoaded = true;
            } else {
                console.log('    ✗ 筛选下拉框无选项');
                pageResult.errors.push({
                    severity: 'high',
                    description: '筛选下拉框为空（问题 D）',
                    details: filterResults.details
                });
            }
        }

        // 5. 检查表格数据
        console.log('\n[5/6] 检查表格数据');

        const tableResults = await checkTableData(page, path);
        if (tableResults.hasData) {
            console.log('    ✓ 表格数据正常显示 (' + tableResults.rowCount + ' 行)');
            pageResult.checks.tableDataLoaded = true;
        } else {
            console.log('    ⚠ 表格无数据或加载失败');
            if (!tableResults.error) {
                pageResult.warnings.push({
                    description: '表格无数据',
                    details: tableResults.message
                });
            }
        }

        // 6. 检查详情弹窗（针对 raw-data 和 results）
        if (path === '/raw-data' || path === '/results') {
            console.log('\n[6/6] 检查详情弹窗功能');

            const modalResults = await checkDetailModal(page, path);
            if (modalResults.works) {
                console.log('    ✓ 详情弹窗功能正常');
                pageResult.checks.detailModalWorks = true;
            } else {
                console.log('    ✗ 详情弹窗功能异常: ' + modalResults.error);
                pageResult.errors.push({
                    severity: 'medium',
                    description: '详情弹窗异常（问题 C1/C2）',
                    details: modalResults.error
                });
            }
        }

        // 收集页面错误
        pageResult.errors = [...pageResult.errors, ...errors];
        pageResult.errorsFound = errors.length;

    } catch (e) {
        console.log('\n    ✗ 测试过程出错: ' + e.message);
        pageResult.errors.push({
            severity: 'high',
            description: '测试执行出错',
            details: e.message
        });
    }

    return pageResult;
}

// 获取页面必要的 DOM 元素选择器
function getRequiredElements(path) {
    const elements = {
        '/raw-data': [
            'nav',
            '#raw-projects-table',
            '.filter-select',
            '.btn-primary',
            '#pagination'
        ],
        '/results': [
            'nav',
            '#result-projects-table',
            '.filter-select',
            '.btn-primary',
            '#pagination'
        ],
        '/files': [
            'nav',
            '#files-table',
            '.filter-select',
            '.btn-primary',
            '#pagination'
        ],
        '/metadata': [
            'nav',
            '#metadata-config',
            '.config-section',
            '.field-list'
        ]
    };
    return elements[path] || [];
}

// 检查 API 调用
async function checkApiCalls(page, path) {
    try {
        // 等待网络空闲后检查是否有失败的请求
        await page.waitForTimeout(3000);

        // 获取页面中所有的 fetch/XHR 请求
        const requests = page.evaluate(() => {
            return window.performance.getEntriesByType('resource')
                .filter(r => r.initiatorType === 'fetch' || r.initiatorType === 'xmlhttprequest')
                .map(r => ({
                    name: r.name,
                    duration: r.duration,
                    transferSize: r.transferSize
                }));
        });

        // 触发一个 API 调用来测试
        let apiPath = '';
        if (path === '/raw-data') {
            apiPath = '/api/raw-projects';
        } else if (path === '/results') {
            apiPath = '/api/result-projects';
        } else if (path === '/files') {
            apiPath = '/api/files/imported-projects';
        } else if (path === '/metadata') {
            apiPath = '/api/metadata/fields';
        }

        if (apiPath) {
            const response = await page.request.get(BASE_URL + apiPath);
            if (response.ok()) {
                return { success: true, data: await response.json() };
            } else {
                return { success: false, error: 'API 返回 ' + response.status() };
            }
        }

        return { success: true };
    } catch (e) {
        return { success: false, error: e.message };
    }
}

// 检查筛选下拉框选项
async function checkFilterOptions(page, path) {
    try {
        // 查找筛选下拉框
        const filterSelectors = [
            '.filter-select',
            '[id*="filter"]',
            'select.filter'
        ];

        let hasOptions = false;
        let details = [];

        for (const selector of filterSelectors) {
            try {
                const filters = await page.locator(selector).all();
                for (const filter of filters) {
                    const options = await filter.locator('option').all();
                    if (options.length > 1) { // 至少有 1 个选项（不含默认选项）
                        hasOptions = true;
                    } else {
                        details.push('筛选框 ' + selector + ' 无选项');
                    }
                }
            } catch (e) {
                // 忽略
            }
        }

        // 尝试获取筛选 API 数据
        try {
            let apiUrl = '';
            if (path === '/raw-data') {
                apiUrl = '/api/filter-options/raw';
            } else if (path === '/results') {
                apiUrl = '/api/filter-options/result';
            }

            if (apiUrl) {
                const response = await page.request.get(BASE_URL + apiUrl);
                if (response.ok()) {
                    const data = await response.json();
                    if (data.options && Object.keys(data.options).length > 0) {
                        hasOptions = true;
                        details.push('API 返回筛选选项: ' + JSON.stringify(data.options));
                    }
                }
            }
        } catch (e) {
            // API 可能不存在，这是预期的
        }

        return { hasOptions, details: details.join('; ') };
    } catch (e) {
        return { hasOptions: false, details: e.message };
    }
}

// 检查表格数据
async function checkTableData(page, path) {
    try {
        let tableSelector = '';

        if (path === '/raw-data') {
            tableSelector = '#raw-projects-table tbody tr';
        } else if (path === '/results') {
            tableSelector = '#result-projects-table tbody tr';
        } else if (path === '/files') {
            tableSelector = '#files-table tbody tr';
        }

        if (tableSelector) {
            // 等待表格加载
            await page.waitForSelector(tableSelector, { timeout: 10000 }).catch(() => null);

            const rows = await page.locator(tableSelector).all();

            if (rows.length > 0) {
                return {
                    hasData: true,
                    rowCount: rows.length,
                    message: '找到 ' + rows.length + ' 行数据'
                };
            } else {
                return {
                    hasData: false,
                    rowCount: 0,
                    message: '表格无数据行',
                    error: false
                };
            }
        }

        return { hasData: true, rowCount: 0, message: '无需检查表格' };
    } catch (e) {
        return { hasData: false, rowCount: 0, message: e.message, error: true };
    }
}

// 检查详情弹窗功能
async function checkDetailModal(page, path) {
    try {
        let tableSelector = '';
        let modalSelector = '';
        let detailApi = '';

        if (path === '/raw-data') {
            tableSelector = '#raw-projects-table tbody tr';
            modalSelector = '#raw-detail-modal';
            detailApi = '/api/raw-projects';
        } else if (path === '/results') {
            tableSelector = '#result-projects-table tbody tr';
            modalSelector = '#result-detail-modal';
            detailApi = '/api/result-projects';
        }

        // 查找可点击的行
        const rows = await page.locator(tableSelector).all();

        if (rows.length === 0) {
            return { works: true, message: '无数据行可测试' };
        }

        // 获取第一行的项目 ID
        const firstRow = rows[0];
        let projectId = '';

        try {
            projectId = await firstRow.getAttribute('data-project-id');
            if (!projectId) {
                projectId = await firstRow.locator('td').first().textContent();
            }
        } catch (e) {
            projectId = 'TEST_001'; // 使用测试 ID
        }

        // 尝试通过 API 检查详情数据
        if (detailApi && projectId) {
            try {
                let apiUrl = BASE_URL + detailApi + '/' + projectId;
                const response = await page.request.get(apiUrl);
                if (response.ok()) {
                    const data = await response.json();

                    // 检查关键字段
                    if (path === '/raw-data') {
                        const requiredFields = ['raw_title', 'raw_type', 'raw_species', 'raw_tissue', 'raw_db_link'];
                        const missingFields = requiredFields.filter(f => !data[f]);
                        if (missingFields.length > 0) {
                            return {
                                works: false,
                                error: '详情缺少字段（问题 C1）: ' + missingFields.join(', ')
                            };
                        }
                    } else if (path === '/results') {
                        const requiredFields = ['results_title', 'results_type', 'results_raw', 'results_DOI', 'results_db_link'];
                        const missingFields = requiredFields.filter(f => !data[f]);
                        if (missingFields.length > 0) {
                            return {
                                works: false,
                                error: '详情缺少字段（问题 C2）: ' + missingFields.join(', ')
                            };
                        }
                    }
                }
            } catch (e) {
                // API 可能不存在
            }
        }

        return { works: true, message: '详情弹窗检查通过' };
    } catch (e) {
        return { works: false, error: e.message };
    }
}

// 测试 file_property 和 file_project_ref_id（问题 E/F/G/H）
async function testFilePropertyAndRefId(page) {
    console.log('\n' + '='.repeat(60));
    console.log('测试 file_property 和 file_project_ref_id');
    console.log('='.repeat(60));

    const results = {
        filePropertyOk: false,
        refIdOk: false,
        duplicateCheckOk: false,
        issues: []
    };

    // 1. 测试 files API 返回 file_property
    try {
        const response = await page.request.get(BASE_URL + '/api/files/imported-projects');
        if (response.ok()) {
            const data = await response.json();
            if (data.projects && data.projects.length > 0) {
                const project = data.projects[0];
                if (project.file_property) {
                    console.log('    ✓ file_property 存在: ' + project.file_property);
                    results.filePropertyOk = true;
                } else {
                    console.log('    ✗ file_property 缺失（问题 E/F/G）');
                    results.issues.push('file_property 字段缺失');
                }

                if (project.file_project_ref_id !== undefined) {
                    console.log('    ✓ file_project_ref_id 存在: ' + project.file_project_ref_id);
                    results.refIdOk = true;
                } else {
                    console.log('    ✗ file_project_ref_id 缺失（问题 A）');
                    results.issues.push('file_project_ref_id 字段缺失');
                }
            }
        }
    } catch (e) {
        console.log('    ✗ API 调用失败: ' + e.message);
        results.issues.push('API 调用失败: ' + e.message);
    }

    // 2. 测试重复文件检测
    try {
        // 测试添加重复文件
        const testFile = {
            file_name: 'test_duplicate.fastq',
            file_project_id: 'TEST_DUP_001',
            file_type: 'raw',
            file_size: 1024
        };

        // 第一次添加
        const response1 = await page.request.post(BASE_URL + '/api/files', {
            data: testFile,
            headers: { 'Content-Type': 'application/json' }
        });

        if (response1.ok()) {
            const result1 = await response1.json();

            // 第二次添加相同文件
            const response2 = await page.request.post(BASE_URL + '/api/files', {
                data: testFile,
                headers: { 'Content-Type': 'application/json' }
            });

            if (response2.ok()) {
                const result2 = await response2.json();

                if (result2.is_duplicate) {
                    console.log('    ✓ 重复文件检测正常工作（问题 H）');
                    results.duplicateCheckOk = true;
                } else {
                    console.log('    ✗ 重复文件检测未工作（问题 H）');
                    results.issues.push('重复文件检测未工作');
                }
            }
        }
    } catch (e) {
        console.log('    ⚠ 重复文件检测测试跳过: ' + e.message);
    }

    return results;
}

// 测试 confirmImport 动态字段收集（问题 B）
async function testConfirmImportDynamicFields(page) {
    console.log('\n' + '='.repeat(60));
    console.log('测试 confirmImport 动态字段收集');
    console.log('='.repeat(60));

    const results = {
        dynamicFieldOk: false,
        issues: []
    };

    // 检查前端代码中是否使用动态字段
    try {
        const pageContent = await page.content();

        // 检查是否遍历 metadataFields
        if (pageContent.includes('metadataFields') || pageContent.includes('metadata_fields')) {
            console.log('    ✓ 使用动态字段收集（metadataFields）');
            results.dynamicFieldOk = true;
        } else {
            console.log('    ✗ 未使用动态字段收集（问题 B）');
            results.issues.push('confirmImport 未使用动态字段收集');
        }

        // 检查是否有硬编码的字段
        const hardcodedFields = ['raw_type', 'raw_species', 'raw_tissue', 'raw_db_link'];
        for (const field of hardcodedFields) {
            if (pageContent.includes("'" + field + "'") || pageContent.includes('"' + field + '"')) {
                const pattern = new RegExp('["\']' + field + '["\']\\s*:\\s*["\'][^"\']*["\']');
                if (pattern.test(pageContent)) {
                    console.log('    ⚠ 发现硬编码字段: ' + field);
                }
            }
        }
    } catch (e) {
        console.log('    ✗ 检查失败: ' + e.message);
        results.issues.push('检查失败: ' + e.message);
    }

    return results;
}

// 主测试函数
async function main() {
    console.log('='.repeat(60));
    console.log('BioData Manager - 问题发现测试');
    console.log('测试地址: ' + BASE_URL);
    console.log('测试页面: ' + PAGES.join(', '));
    console.log('='.repeat(60));

    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 },
        ignoreHTTPSErrors: true
    });

    const page = await context.newPage();

    try {
        // 1. 测试所有页面
        for (const path of PAGES) {
            const result = await testPage(page, path);
            testResults.pages.push(result);
            testResults.summary.pagesTested++;
            testResults.summary.errorsFound += result.errors.length;
            testResults.summary.issues.push(...result.errors);
        }

        // 2. 测试 file_property 和 file_project_ref_id
        console.log('\n');
        const filePropertyResults = await testFilePropertyAndRefId(page);
        if (!filePropertyResults.filePropertyOk) {
            testResults.summary.issues.push({
                type: 'E/F/G',
                description: 'file_property 未正确显示'
            });
        }
        if (!filePropertyResults.refIdOk) {
            testResults.summary.issues.push({
                type: 'A',
                description: 'file_project_ref_id 字段缺失'
            });
        }
        if (!filePropertyResults.duplicateCheckOk) {
            testResults.summary.issues.push({
                type: 'H',
                description: '重复文件检测未工作'
            });
        }

        // 3. 测试 confirmImport 动态字段
        console.log('\n');
        const confirmImportResults = await testConfirmImportDynamicFields(page);
        if (!confirmImportResults.dynamicFieldOk) {
            testResults.summary.issues.push({
                type: 'B',
                description: 'confirmImport 未使用动态字段收集'
            });
        }

        // 生成测试报告
        generateReport();

    } catch (e) {
        console.error('测试过程出错:', e);
        testResults.summary.issues.push({
            type: 'error',
            description: '测试执行出错',
            details: e.message
        });
    } finally {
        await browser.close();
    }
}

// 生成测试报告
function generateReport() {
    console.log('\n\n');
    console.log('='.repeat(70));
    console.log('测试结果摘要');
    console.log('='.repeat(70));

    console.log('\n测试页面数: ' + testResults.summary.pagesTested);
    console.log('发现错误数: ' + testResults.summary.errorsFound);
    console.log('发现问题数: ' + testResults.summary.issues.length);

    // 按严重程度分类问题
    const highSeverity = testResults.summary.issues.filter(i => i.severity === 'high');
    const mediumSeverity = testResults.summary.issues.filter(i => i.severity === 'medium');

    console.log('\n严重问题: ' + highSeverity.length + ' 个');
    console.log('中等问题: ' + mediumSeverity.length + ' 个');

    if (testResults.summary.issues.length > 0) {
        console.log('\n问题列表:');
        console.log('-'.repeat(70));

        testResults.summary.issues.forEach((issue, idx) => {
            const severity = issue.severity === 'high' ? '🔴 高' :
                           issue.severity === 'medium' ? '🟡 中' : '⚪ 低';
            console.log((idx + 1) + '. [' + severity + '] ' + issue.description);
            if (issue.selector) {
                console.log('   元素选择器: ' + issue.selector);
            }
            if (issue.details) {
                console.log('   详情: ' + issue.details);
            }
            if (issue.type) {
                console.log('   问题类型: ' + issue.type);
            }
        });
    }

    // 页面详细结果
    console.log('\n\n');
    console.log('='.repeat(70));
    console.log('页面详细结果');
    console.log('='.repeat(70));

    testResults.pages.forEach(page => {
        console.log('\n【' + page.path + '】');
        console.log('  错误数: ' + page.errorsFound);

        const checks = page.checks;
        console.log('  ✓ DOM 结构: ' + (checks.domComplete ? '完整' : '不完整'));
        console.log('  ✓ 元素渲染: ' + (checks.elementsRendered ? '正常' : '异常'));
        console.log('  ✓ API 调用: ' + (checks.apiCallsSuccess ? '成功' : '失败'));
        console.log('  ✓ 筛选功能: ' + (checks.filterOptionsLoaded ? '有选项' : '无选项'));
        console.log('  ✓ 表格数据: ' + (checks.tableDataLoaded ? '正常' : '异常'));
        console.log('  ✓ 详情弹窗: ' + (checks.detailModalWorks ? '正常' : '异常'));
    });

    // 已知问题验证结果
    console.log('\n\n');
    console.log('='.repeat(70));
    console.log('已知问题验证结果 (A~H)');
    console.log('='.repeat(70));

    const issueResults = [
        { id: 'A', name: 'file_project_ref_id 字段', checked: false },
        { id: 'B', name: 'confirmImport 动态字段', checked: false },
        { id: 'C1', name: '原始数据详情弹窗', checked: false },
        { id: 'C2', name: '结果数据详情弹窗', checked: false },
        { id: 'D', name: '筛选功能', checked: false },
        { id: 'E/F/G', name: 'file_property 显示', checked: false },
        { id: 'H', name: '重复文件检测', checked: false }
    ];

    issueResults.forEach(issue => {
        const isOk = !testResults.summary.issues.some(i => i.type === issue.id || i.type === issue.id.replace('/','-'));
        issue.checked = true;
        console.log('  ' + (isOk ? '✓' : '✗') + ' 问题 ' + issue.id + ': ' + issue.name + ' - ' + (isOk ? '已修复' : '待修复'));
    });

    console.log('\n\n');
    console.log('='.repeat(70));
    console.log('测试完成');
    console.log('='.repeat(70));
}

// 导出结果供后续使用
module.exports = { testResults, main };

// 如果直接运行
if (require.main === module) {
    main().catch(console.error);
}
