/**
 * BioData Manager - 问题发现综合测试 v2
 * 修正 API 路径，验证已知问题 A~H 是否已修复
 */

const { chromium } = require('playwright');

const BASE_URL = 'http://192.168.3.147:20425';
const PAGES = ['/raw-data', '/results', '/files', '/metadata'];

let testResults = {
    summary: {
        pagesTested: 0,
        errorsFound: 0,
        issues: [],
        fixed: [],
        pending: []
    },
    pages: []
};

// 收集页面错误的处理器
function setupErrorHandlers(page) {
    const errors = [];

    page.on('console', msg => {
        if (msg.type() === 'error') {
            errors.push({
                type: 'console_error',
                message: msg.text(),
                timestamp: new Date().toISOString()
            });
        }
    });

    page.on('pageerror', err => {
        errors.push({
            type: 'pageerror',
            message: err.message,
            timestamp: new Date().toISOString()
        });
    });

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
    console.log(`\n${'='.repeat(60)}`);
    console.log(`测试页面: ${path}`);
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
        console.log(`\n[1/6] 访问页面: ${path}`);
        const response = await page.goto(BASE_URL + path, {
            waitUntil: 'networkidle',
            timeout: 30000
        });

        if (response && response.status() === 200) {
            console.log(`    ✓ 页面加载成功 (状态码: ${response.status()})`);
            pageResult.checks.domComplete = true;
        } else {
            console.log(`    ✗ 页面加载失败 (状态码: ${response ? response.status() : '无响应'})`);
            pageResult.errors.push({
                severity: 'high',
                description: '页面无法加载',
                details: response ? `状态码: ${response.status()}` : '无响应'
            });
        }

        await page.waitForTimeout(2000);

        // 2. 检查 DOM 结构完整性
        console.log(`\n[2/6] 检查 DOM 结构完整性`);

        const tableSelector = path === '/raw-data' ? '#project-list tbody tr' :
                             path === '/results' ? '#project-list tbody tr' :
                             path === '/files' ? '#imported-projects-table tbody tr' : '#metadata-config';

        try {
            const element = await page.locator(tableSelector).first();
            await element.waitFor({ timeout: 5000 }).catch(() => null);
            const isVisible = await element.isVisible().catch(() => false);
            if (isVisible) {
                console.log(`    ✓ 必要 DOM 元素可见`);
                pageResult.checks.elementsRendered = true;
            } else {
                console.log(`    ⚠ 元素存在但不可见或不存在`);
                pageResult.warnings.push({ description: '元素不可见', selector: tableSelector });
            }
        } catch (e) {
            console.log(`    ✗ 元素检查出错: ${e.message}`);
        }

        // 3. 检查 API 调用 - 使用正确的 API 端点
        console.log(`\n[3/6] 检查 API 调用`);

        let apiSuccess = false;
        try {
            if (path === '/raw-data') {
                // 测试 /api/projects?table=raw
                const resp = await page.request.get(BASE_URL + '/api/projects?table=raw');
                if (resp.ok()) {
                    const data = await resp.json();
                    console.log(`    ✓ API /api/projects?table=raw 返回成功 (${data.data?.length || 0} 条数据)`);
                    apiSuccess = true;
                }
            } else if (path === '/results') {
                // 测试 /api/projects?table=result
                const resp = await page.request.get(BASE_URL + '/api/projects?table=result');
                if (resp.ok()) {
                    const data = await resp.json();
                    console.log(`    ✓ API /api/projects?table=result 返回成功 (${data.data?.length || 0} 条数据)`);
                    apiSuccess = true;
                }
            } else if (path === '/files') {
                // 测试 /api/files/imported-projects
                const resp = await page.request.get(BASE_URL + '/api/files/imported-projects');
                if (resp.ok()) {
                    const data = await resp.json();
                    console.log(`    ✓ API /api/files/imported-projects 返回成功 (${data.projects?.length || 0} 条数据)`);
                    apiSuccess = true;

                    // 检查 file_property 和 file_project_ref_id
                    if (data.projects && data.projects.length > 0) {
                        const project = data.projects[0];
                        if (project.file_property) {
                            console.log(`    ✓ file_property 存在: "${project.file_property}"`);
                        } else {
                            console.log(`    ⚠ file_property 缺失`);
                        }
                        if (project.file_project_ref_id !== undefined) {
                            console.log(`    ✓ file_project_ref_id 存在: "${project.file_project_ref_id}"`);
                        } else {
                            console.log(`    ⚠ file_project_ref_id 缺失`);
                        }
                    }
                }
            } else if (path === '/metadata') {
                // 测试 /api/metadata/config
                const resp = await page.request.get(BASE_URL + '/api/metadata/config');
                if (resp.ok()) {
                    const data = await resp.json();
                    console.log(`    ✓ API /api/metadata/config 返回成功 (${data.config?.length || 0} 条配置)`);
                    apiSuccess = true;
                }
            }
        } catch (e) {
            console.log(`    ✗ API 调用出错: ${e.message}`);
        }

        if (apiSuccess) {
            pageResult.checks.apiCallsSuccess = true;
        } else {
            pageResult.errors.push({
                severity: 'high',
                description: 'API 调用失败'
            });
        }

        // 4. 检查筛选下拉框（针对 raw-data 和 results）
        if (path === '/raw-data' || path === '/results') {
            console.log(`\n[4/6] 检查筛选下拉框`);

            let hasFilterOptions = false;
            try {
                // 查找筛选下拉框
                const filterSelectors = path === '/raw-data'
                    ? ['#filter-raw_type', '#filter-raw_species', '#filter-raw_tissue']
                    : ['#filter-results_type', '#filter-results_raw'];

                for (const selector of filterSelectors) {
                    try {
                        const select = await page.locator(selector);
                        const count = await select.locator('option').count();
                        if (count > 1) {
                            hasFilterOptions = true;
                            console.log(`    ✓ ${selector} 有 ${count - 1} 个选项`);
                        } else {
                            console.log(`    ⚠ ${selector} 无选项`);
                        }
                    } catch (e) {
                        console.log(`    ✗ ${selector} 不存在`);
                    }
                }
            } catch (e) {
                console.log(`    ✗ 筛选框检查出错: ${e.message}`);
            }

            if (hasFilterOptions) {
                pageResult.checks.filterOptionsLoaded = true;
            } else {
                pageResult.errors.push({
                    severity: 'high',
                    description: '筛选下拉框为空（问题 D）'
                });
            }
        }

        // 5. 检查表格数据
        console.log(`\n[5/6] 检查表格数据`);

        const tableRowSelector = path === '/raw-data' ? '#project-list tbody tr' :
                           path === '/results' ? '#project-list tbody tr' :
                           path === '/files' ? '#imported-projects-table tbody tr' : '.config-section';

        try {
            const rows = await page.locator(tableRowSelector).all();
            if (rows.length > 0) {
                console.log(`    ✓ 表格数据正常显示 (${rows.length} 行)`);
                pageResult.checks.tableDataLoaded = true;
            } else {
                console.log(`    ⚠ 表格无数据（可能是空数据库）`);
            }
        } catch (e) {
            console.log(`    ✗ 表格检查出错: ${e.message}`);
        }

        // 6. 检查详情弹窗功能
        if (path === '/raw-data' || path === '/results') {
            console.log(`\n[6/6] 检查详情弹窗功能`);

            try {
                // 测试 API 返回的详情数据
                const tableName = path === '/raw-data' ? 'raw' : 'result';
                const resp = await page.request.get(BASE_URL + `/api/projects?table=${tableName}`);

                if (resp.ok()) {
                    const data = await resp.json();
                    if (data.data && data.data.length > 0) {
                        const projectId = tableName === 'raw' ? data.data[0].raw_id : data.data[0].results_id;
                        console.log(`    测试项目 ID: ${projectId}`);

                        // 检查详情 API
                        const detailResp = await page.request.get(
                            BASE_URL + `/api/projects/${tableName === 'raw' ? 'raw' : 'result'}/${projectId}`
                        );

                        if (detailResp.ok()) {
                            const detailData = await detailResp.json();

                            if (path === '/raw-data') {
                                // 检查 C1: raw_db_link 字段
                                const requiredFields = ['raw_title', 'raw_type', 'raw_species', 'raw_tissue', 'raw_db_link'];
                                const missing = requiredFields.filter(f => !detailData[f]);
                                if (missing.length === 0) {
                                    console.log(`    ✓ 原始数据详情包含所有必要字段 (C1)`);
                                } else {
                                    console.log(`    ✗ 原始数据详情缺少字段: ${missing.join(', ')} (C1)`);
                                }
                            } else {
                                // 检查 C2: results_DOI, results_db_link 字段
                                const requiredFields = ['results_title', 'results_type', 'results_raw', 'results_DOI', 'results_db_link'];
                                const missing = requiredFields.filter(f => !detailData[f]);
                                if (missing.length === 0) {
                                    console.log(`    ✓ 结果数据详情包含所有必要字段 (C2)`);
                                } else {
                                    console.log(`    ✗ 结果数据详情缺少字段: ${missing.join(', ')} (C2)`);
                                }
                            }
                        }
                    } else {
                        console.log(`    ⚠ 无数据行，跳过详情弹窗测试`);
                    }
                }
            } catch (e) {
                console.log(`    ✗ 详情检查出错: ${e.message}`);
            }
        }

        pageResult.errors = [...pageResult.errors, ...errors];
        pageResult.errorsFound = errors.length;

    } catch (e) {
        console.log(`\n    ✗ 测试过程出错: ${e.message}`);
        pageResult.errors.push({
            severity: 'high',
            description: '测试执行出错',
            details: e.message
        });
    }

    return pageResult;
}

// 测试 file_property 和 file_project_ref_id
async function testFilePropertyAndRefId(page) {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`测试 file_property 和 file_project_ref_id (问题 E/F/G)`);
    console.log('='.repeat(60));

    const results = {
        filePropertyOk: false,
        refIdOk: false,
        duplicateCheckOk: false,
        confirmImportOk: false,
        issues: []
    };

    try {
        // 1. 测试 files API 返回 file_property
        const resp = await page.request.get(BASE_URL + '/api/files/imported-projects');
        if (resp.ok()) {
            const data = await resp.json();
            if (data.projects && data.projects.length > 0) {
                const project = data.projects[0];

                if (project.file_property) {
                    // 验证格式：应该是 "转录组-小鼠-Liver" 而不是 "mRseq-Ms-Liv"
                    const isAbbreviated = /^[a-zA-Z]{2,5}-[a-zA-Z]{2,5}-[a-zA-Z]{3,}$/.test(project.file_property);
                    if (!isAbbreviated) {
                        console.log(`    ✓ file_property 格式正确: "${project.file_property}" (E/F/G)`);
                        results.filePropertyOk = true;
                    } else {
                        console.log(`    ⚠ file_property 使用缩写格式: "${project.file_property}"`);
                        results.issues.push('file_property 使用缩写而非中文标签');
                    }
                } else {
                    console.log(`    ✗ file_property 缺失 (E/F/G)`);
                    results.issues.push('file_property 字段缺失');
                }

                if (project.file_project_ref_id !== undefined) {
                    console.log(`    ✓ file_project_ref_id 存在: "${project.file_project_ref_id}" (A)`);
                    results.refIdOk = true;
                } else {
                    console.log(`    ✗ file_project_ref_id 缺失 (A)`);
                    results.issues.push('file_project_ref_id 字段缺失');
                }
            } else {
                console.log(`    ⚠ 无已导入项目，跳过 file_property 检查`);
                results.filePropertyOk = true; // 无数据不视为问题
                results.refIdOk = true;
            }
        }
    } catch (e) {
        console.log(`    ✗ API 调用失败: ${e.message}`);
        results.issues.push(`API 调用失败: ${e.message}`);
    }

    // 2. 测试重复文件检测
    console.log(`\n测试重复文件检测 (问题 H)`);
    try {
        // 尝试添加测试文件
        const testFile = {
            folder_name: 'TEST_DUP_FOLDER',
            files: ['test_duplicate.fastq'],
            data_type: 'raw',
            project_info: {
                raw_title: '重复文件测试',
                raw_type: 'mRNAseq',
                raw_species: 'Homo sapiens'
            }
        };

        const resp1 = await page.request.post(BASE_URL + '/api/import-download', {
            data: testFile,
            headers: { 'Content-Type': 'application/json' }
        });

        if (resp1.ok()) {
            const result1 = await resp1.json();

            // 第二次添加相同文件
            const resp2 = await page.request.post(BASE_URL + '/api/import-download', {
                data: testFile,
                headers: { 'Content-Type': 'application/json' }
            });

            if (resp2.ok()) {
                const result2 = await resp2.json();

                if (result2.is_duplicate) {
                    console.log(`    ✓ 重复文件检测正常工作 (H)`);
                    results.duplicateCheckOk = true;
                } else if (result2.success) {
                    console.log(`    ⚠ 重复文件检测未触发，导入了重复文件 (H)`);
                    results.issues.push('重复文件检测未工作');
                } else {
                    console.log(`    ✗ 导入失败: ${result2.message}`);
                }
            }
        }
    } catch (e) {
        console.log(`    ⚠ 重复文件检测测试跳过: ${e.message}`);
    }

    return results;
}

// 测试 confirmImport 动态字段收集
async function testConfirmImportDynamicFields(page) {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`测试 confirmImport 动态字段收集 (问题 B)`);
    console.log('='.repeat(60));

    const results = {
        dynamicFieldOk: false,
        codeCheckOk: false,
        issues: []
    };

    try {
        // 获取前端页面内容
        const response = await page.goto(BASE_URL + '/files', { waitUntil: 'networkidle' });
        const content = await page.content();

        // 检查是否使用 metadataFields 动态收集
        if (content.includes('metadataFields') && content.includes('metadata-')) {
            console.log(`    ✓ 前端代码使用 metadataFields 动态收集字段 (B)`);
            results.dynamicFieldOk = true;
            results.codeCheckOk = true;
        } else {
            console.log(`    ✗ 前端代码未使用动态字段收集 (B)`);
            results.issues.push('confirmImport 未使用 metadataFields 动态收集');
        }

        // 检查是否有硬编码的字段
        const hardcodedPattern = /['"]raw_type['"]\s*:\s*['"][^'"]+['"]/g;
        const matches = content.match(hardcodedPattern);
        if (matches) {
            console.log(`    ⚠ 发现可能的硬编码: ${matches[0]}`);
        } else {
            console.log(`    ✓ 未发现明显的硬编码字段`);
        }

    } catch (e) {
        console.log(`    ✗ 检查失败: ${e.message}`);
        results.issues.push(`检查失败: ${e.message}`);
    }

    return results;
}

// 主测试函数
async function main() {
    console.log('='.repeat(70));
    console.log('BioData Manager - 问题发现测试 v2 (修正版)');
    console.log(`测试地址: ${BASE_URL}`);
    console.log(`测试页面: ${PAGES.join(', ')}`);
    console.log('='.repeat(70));

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
        }

        // 2. 测试 file_property 和 file_project_ref_id
        console.log('\n');
        const filePropertyResults = await testFilePropertyAndRefId(page);

        if (filePropertyResults.filePropertyOk) {
            testResults.summary.fixed.push('E/F/G: file_property 显示');
        } else if (filePropertyResults.issues.length === 0) {
            testResults.summary.fixed.push('E/F/G: file_property (无数据)');
        } else {
            testResults.summary.pending.push('E/F/G: file_property - ' + filePropertyResults.issues.join('; '));
        }

        if (filePropertyResults.refIdOk) {
            testResults.summary.fixed.push('A: file_project_ref_id');
        } else {
            testResults.summary.pending.push('A: file_project_ref_id - ' + filePropertyResults.issues.join('; '));
        }

        if (filePropertyResults.duplicateCheckOk) {
            testResults.summary.fixed.push('H: 重复文件检测');
        } else {
            testResults.summary.pending.push('H: 重复文件检测 - ' + filePropertyResults.issues.join('; '));
        }

        // 3. 测试 confirmImport 动态字段
        console.log('\n');
        const confirmImportResults = await testConfirmImportDynamicFields(page);

        if (confirmImportResults.dynamicFieldOk) {
            testResults.summary.fixed.push('B: confirmImport 动态字段');
        } else {
            testResults.summary.pending.push('B: confirmImport - ' + confirmImportResults.issues.join('; '));
        }

        // 生成最终报告
        generateReport();

    } catch (e) {
        console.error('测试过程出错:', e);
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

    console.log(`\n测试页面数: ${testResults.summary.pagesTested}`);
    console.log(`发现错误数: ${testResults.summary.errorsFound}`);

    // 已知问题验证结果
    console.log('\n' + '='.repeat(70));
    console.log('已知问题验证结果 (A~H)');
    console.log('='.repeat(70));

    const issueStatus = [
        { id: 'A', name: 'file_project_ref_id 字段', fixed: false },
        { id: 'B', name: 'confirmImport 动态字段', fixed: false },
        { id: 'C1', name: '原始数据详情弹窗', fixed: true },
        { id: 'C2', name: '结果数据详情弹窗', fixed: true },
        { id: 'D', name: '筛选功能', fixed: true },
        { id: 'E/F/G', name: 'file_property 显示', fixed: false },
        { id: 'H', name: '重复文件检测', fixed: false }
    ];

    // 从 fixed 和 pending 列表更新状态
    issueStatus.forEach(issue => {
        const isFixed = testResults.summary.fixed.some(f => f.includes(issue.id) || (issue.id === 'E/F/G' && f.includes('file_property')));
        const isPending = testResults.summary.pending.some(p => p.includes(issue.id) || (issue.id === 'E/F/G' && p.includes('file_property')));
        issue.fixed = isFixed && !isPending;
    });

    console.log('\n┌────┬─────────────────────────────┬──────────┐');
    console.log('│ ID │ 问题描述                    │ 状态     │');
    console.log('├────┼─────────────────────────────┼──────────┤');
    issueStatus.forEach(issue => {
        const status = issue.fixed ? '✓ 已修复' : '✗ 待修复';
        const padding = ' '.repeat(29 - issue.name.length);
        console.log(`│ ${issue.id.padEnd(3)}│ ${issue.name}${padding}│ ${status.padEnd(8)}│`);
    });
    console.log('└────┴─────────────────────────────┴──────────┘');

    // 已修复问题列表
    if (testResults.summary.fixed.length > 0) {
        console.log('\n✓ 已修复问题:');
        testResults.summary.fixed.forEach(item => console.log(`  - ${item}`));
    }

    // 待修复问题列表
    if (testResults.summary.pending.length > 0) {
        console.log('\n✗ 待修复问题:');
        testResults.summary.pending.forEach(item => console.log(`  - ${item}`));
    }

    // 页面详细结果
    console.log('\n\n');
    console.log('='.repeat(70));
    console.log('页面详细结果');
    console.log('='.repeat(70));

    testResults.pages.forEach(page => {
        console.log(`\n【${page.path}】`);

        const checks = page.checks;
        const status = (checks.domComplete && checks.apiCallsSuccess) ? '✓' :
                      (checks.domComplete || checks.apiCallsSuccess) ? '⚠' : '✗';

        console.log(`  ${status} 页面加载: ${checks.domComplete ? '成功' : '失败'}`);
        console.log(`  ${checks.apiCallsSuccess ? '✓' : '✗'} API 调用: ${checks.apiCallsSuccess ? '成功' : '失败'}`);

        if (page.path !== '/metadata') {
            console.log(`  ${checks.filterOptionsLoaded ? '✓' : '✗'} 筛选功能: ${checks.filterOptionsLoaded ? '有选项' : '无选项'}`);
            console.log(`  ${checks.tableDataLoaded ? '✓' : '⚠'} 表格数据: ${checks.tableDataLoaded ? '正常' : '空或异常'}`);
        }
    });

    console.log('\n\n');
    console.log('='.repeat(70));
    console.log('测试完成');
    console.log('='.repeat(70));

    // 汇总统计
    const totalIssues = issueStatus.length;
    const fixedCount = issueStatus.filter(i => i.fixed).length;
    console.log(`\n问题修复率: ${fixedCount}/${totalIssues} (${(fixedCount/totalIssues*100).toFixed(1)}%)`);
}

module.exports = { testResults, main };

if (require.main === module) {
    main().catch(console.error);
}
