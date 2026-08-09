const { chromium } = require('playwright');

const baseURL = process.env.BASE_URL || 'http://127.0.0.1:8000';
const email = process.env.TEST_EMAIL || `browser-e2e-${Date.now()}@example.com`;
const password = process.env.TEST_PASSWORD || 'browser-e2e-password-2026';
const facility = `Browser E2E Facility ${Date.now()}`;

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function attachGuards(page, label, errors) {
  page.on('pageerror', error => errors.push(`${label}: pageerror: ${error.message}`));
  page.on('console', msg => {
    if (msg.type() === 'error') errors.push(`${label}: console error: ${msg.text()}`);
  });
  await page.addInitScript(() => {
    window.__cspViolations = [];
    document.addEventListener('securitypolicyviolation', event => {
      window.__cspViolations.push({
        blockedURI: event.blockedURI,
        violatedDirective: event.violatedDirective,
        effectiveDirective: event.effectiveDirective,
      });
    });
  });
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ acceptDownloads: true });
  const page = await context.newPage();
  const browserErrors = [];
  await attachGuards(page, 'main', browserErrors);

  try {
    const response = await page.goto(baseURL, { waitUntil: 'networkidle' });
    assert(response && response.ok(), `home page failed: ${response && response.status()}`);
    const headers = response.headers();
    assert((headers['content-security-policy'] || '').includes("style-src 'self'"), 'strict CSP missing');
    assert(headers['cache-control'] === 'no-store', 'no-store cache policy missing');
    assert(headers['x-content-type-options'] === 'nosniff', 'nosniff missing');
    assert(headers['x-frame-options'] === 'DENY', 'frame denial missing');

    await page.getByRole('heading', { name: 'Ready Set Solutions' }).waitFor();
    await page.locator('#email').fill(email);
    await page.locator('#password').fill(password);
    await page.locator('#registerBtn').click();
    await page.locator('#authMsg').filter({ hasText: 'Registered' }).waitFor();

    await page.locator('#loginBtn').click();
    await page.locator('#app:not(.hidden)').waitFor();
    await page.locator('#who').filter({ hasText: email }).waitFor();

    const storageAfterLogin = await page.evaluate(() => ({
      sessionToken: sessionStorage.getItem('cb_token'),
      localToken: localStorage.getItem('cb_token'),
    }));
    assert(storageAfterLogin.sessionToken, 'auth token was not stored in sessionStorage');
    assert(storageAfterLogin.localToken === null, 'auth token leaked into localStorage');

    await page.locator('#binderName').fill(facility);
    await page.locator('#binderIndustry').selectOption('assisted_living');
    await page.locator('#createBinderBtn').click();
    await page.locator('#binderList').getByText(facility).waitFor();
    await page.locator('#binderList').getByText(facility).click();
    await page.locator('#binderTitle').filter({ hasText: facility }).waitFor();

    await page.locator('button[data-tab="tasks"]').click();
    await page.locator('#taskList').getByText('[ADMIN] Facility license and scope review').waitFor();
    const openTaskCount = await page.locator('#taskList li').count();
    assert(openTaskCount >= 16, `expected seeded assisted-living checklist, got ${openTaskCount} tasks`);

    await page.locator('button[data-tab="docs"]').click();
    await page.locator('#docNote').fill('Browser E2E authorized evidence');
    await page.locator('#docFile').setInputFiles({
      name: 'e2e-evidence.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\n'),
    });
    await page.locator('#uploadDocBtn').click();
    await page.locator('#docList').getByText('e2e-evidence.pdf').waitFor();

    await page.locator('#logoutBtn').click();
    await page.locator('#auth:not(.hidden)').waitFor();
    const storageAfterLogout = await page.evaluate(() => ({
      sessionToken: sessionStorage.getItem('cb_token'),
      sessionEmail: sessionStorage.getItem('cb_email'),
    }));
    assert(storageAfterLogout.sessionToken === null, 'session token survived logout');
    assert(storageAfterLogout.sessionEmail === null, 'session email survived logout');

    await page.locator('#email').fill(email);
    await page.locator('#password').fill(password);
    await page.locator('#loginBtn').click();
    await page.locator('#app:not(.hidden)').waitFor();
    await page.locator('#binderList').getByText(facility).waitFor();
    await page.locator('#binderList').getByText(facility).click();
    await page.locator('button[data-tab="docs"]').click();
    await page.locator('#docList').getByText('e2e-evidence.pdf').waitFor();

    await page.locator('button[data-tab="report"]').click();
    const popupPromise = page.waitForEvent('popup');
    await page.locator('#openReportBtn').click();
    const popup = await popupPromise;
    await attachGuards(popup, 'report', browserErrors);
    await popup.waitForLoadState('domcontentloaded');
    await popup.getByRole('heading', { name: facility }).waitFor();
    await popup.getByText('[ADMIN] Facility license and scope review').waitFor();

    const mainCsp = await page.evaluate(() => window.__cspViolations || []);
    const popupCsp = await popup.evaluate(() => window.__cspViolations || []).catch(() => []);
    if (mainCsp.length) browserErrors.push(`main CSP violations: ${JSON.stringify(mainCsp)}`);
    if (popupCsp.length) browserErrors.push(`report CSP violations: ${JSON.stringify(popupCsp)}`);

    await page.waitForTimeout(300);
    assert(browserErrors.length === 0, `browser security/runtime errors:\n${browserErrors.join('\n')}`);

    console.log(JSON.stringify({
      ok: true,
      facility,
      seededTasks: openTaskCount,
      evidence: 'e2e-evidence.pdf',
      strictCsp: true,
      sessionScopedAuth: true,
      reportPopup: true,
    }));
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error(error.stack || error.message || error);
  process.exit(1);
});
