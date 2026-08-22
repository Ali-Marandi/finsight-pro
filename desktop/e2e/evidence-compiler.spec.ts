import { expect, test, type Page, type Route } from '@playwright/test';

const taxAuditReady = {
  kind: 'tax_audit_pdf',
  manifest: {
    file_name: 'tax_audit_2025.pdf', file_hash: 'a'.repeat(64), source_type: 'pdf', sheet_name: '',
    imported_at: '2026-08-23T09:00:00Z', detected_locale: 'en', row_count: 18, column_count: 0,
  },
  extraction_mode: 'digital_pdf_text',
  ready_for_review: true,
  facts: [
    { concept_id: 'tax_declared', value: 1000, period: '2025', currency: 'USD', scale: 'unit', locations: [{ file_name: 'tax_audit_2025.pdf', sheet_name: '', column_name: '', row_number: null, page_number: 1, table_index: 1, cell_reference: 'R4' }] },
    { concept_id: 'tax_assessed', value: 1250, period: '2025', currency: 'USD', scale: 'unit', locations: [{ file_name: 'tax_audit_2025.pdf', sheet_name: '', column_name: '', row_number: null, page_number: 2, table_index: 1, cell_reference: 'R9' }] },
  ],
  issues: [{ rule_id: 'tax_assessment_reconciliation_difference', severity: 'warning', status: 'fail', message: 'Assessment differs from declared tax plus adjustment.', remediation: 'Verify the adjustment and assessment source pages.', evidence_locations: [{ file_name: 'tax_audit_2025.pdf', sheet_name: '', column_name: '', row_number: null, page_number: 1, table_index: 1, cell_reference: 'R4' }] }],
};

const taxAuditBlocked = {
  ...taxAuditReady,
  ready_for_review: false,
  facts: [],
  issues: [{ rule_id: 'pdf_requires_ocr', severity: 'blocking', status: 'fail', message: 'The PDF contains no machine-readable text.', remediation: 'Run OCR or request a digital source document.', evidence_locations: [] }],
};

const financialStatement = {
  kind: 'financial_statement',
  manifest: {
    file_name: 'statement.xlsx', file_hash: 'b'.repeat(64), source_type: 'xlsx', sheet_name: 'Statement',
    imported_at: '2026-08-23T09:00:00Z', detected_locale: 'en', row_count: 12, column_count: 5,
  },
  mappings: [{ source_column: 'Sales', concept_id: 'revenue', confidence: 0.93, rationale: 'Recognized alias for revenue.', status: 'suggested' }],
  health: { info: 0, warning: 0, blocking: 1 },
  ready_for_analysis: false,
  issues: [{ rule_id: 'mapping_confirmation_required', severity: 'blocking', status: 'fail', message: 'A mapping must be confirmed.', remediation: 'Confirm the detected revenue alias.' }],
};

async function mockEvidenceInspection(page: Page, payload: object) {
  await page.route('**/api/v1/evidence/inspect', async (route: Route) => {
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify(payload) });
  });
}

async function selectEvidenceFile(page: Page, name: string, mimeType: string) {
  await page.locator('input[type="file"]').setInputFiles({ name, mimeType, buffer: Buffer.from('%PDF-1.4 synthetic test document') });
}

test('dashboard directs users to Evidence-first review instead of direct analysis', async ({ page }) => {
  await page.goto('/');

  await expect(page.getByRole('heading', { name: 'Evidence Compiler' })).toBeVisible();
  await page.getByRole('link', { name: 'Start evidence review' }).click();
  await expect(page).toHaveURL(/#\/analysis$/);
  await expect(page.getByText('Drag & drop a financial statement')).toBeVisible();
});

test('tax-audit PDF displays cited facts and reviewer warnings', async ({ page }) => {
  await mockEvidenceInspection(page, taxAuditReady);
  await page.goto('/#/analysis');
  await selectEvidenceFile(page, 'tax_audit_2025.pdf', 'application/pdf');

  await expect(page.getByRole('heading', { name: 'tax_audit_2025.pdf' })).toBeVisible();
  await expect(page.getByText('Tax Audit Evidence Review')).toBeVisible();
  await expect(page.getByText('Tax Declared')).toBeVisible();
  await expect(page.getByText('Tax Assessed')).toBeVisible();
  await expect(page.getByText('Page 1 · Table 1 · R4').first()).toBeVisible();
  await expect(page.getByText('Assessment differs from declared tax plus adjustment.')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Continue to financial analysis' })).toBeVisible();
});

test('PDF without readable text blocks automatic continuation and requires review', async ({ page }) => {
  await mockEvidenceInspection(page, taxAuditBlocked);
  await page.goto('/#/analysis');
  await selectEvidenceFile(page, 'scanned_tax_audit.pdf', 'application/pdf');

  await expect(page.getByText('Evidence requires OCR or manual review')).toBeVisible();
  await expect(page.getByText('The PDF contains no machine-readable text.')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Continue to financial analysis' })).toHaveCount(0);
});

test('spreadsheet aliases remain in mapping review until a reviewer confirms them', async ({ page }) => {
  await mockEvidenceInspection(page, financialStatement);
  await page.goto('/#/analysis');
  await selectEvidenceFile(page, 'statement.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');

  await expect(page.getByRole('heading', { name: 'statement.xlsx' })).toBeVisible();
  await expect(page.getByText('Review proposed mappings')).toBeVisible();
  await expect(page.getByText('Sales')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Confirm and recheck' })).toBeVisible();
});
