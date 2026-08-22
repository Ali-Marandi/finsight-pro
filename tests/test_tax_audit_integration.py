"""Integration coverage for the tax-audit PDF Evidence Compiler workflow."""

import io
import sys
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

PROJECT_ROOT = Path(__file__).parents[1]
API_ROOT = PROJECT_ROOT / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.routers.evidence import router


def evidence_client() -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/evidence")
    return TestClient(app)


def tax_report_pdf(*pages: list[str]) -> bytes:
    """Create a text-based multi-page tax report to exercise the complete API path."""
    buffer = io.BytesIO()
    document = canvas.Canvas(buffer)
    for page_index, page_lines in enumerate(pages):
        y_position = 760
        for line in page_lines:
            document.drawString(72, y_position, line)
            y_position -= 28
        if page_index < len(pages) - 1:
            document.showPage()
    document.save()
    return buffer.getvalue()


def inspect_pdf(pdf: bytes, overrides: str | None = None):
    data = {"mapping_overrides": overrides} if overrides else None
    return evidence_client().post(
        "/api/v1/evidence/inspect",
        data=data,
        files={"file": ("complex_tax_audit.pdf", pdf, "application/pdf")},
    )


class TaxAuditEvidenceIntegrationTests(unittest.TestCase):
    def test_multi_page_conflicting_assessed_tax_is_reviewable_with_page_citations(self):
        response = inspect_pdf(tax_report_pdf(
            [
                "Tax Audit Report 2025 (USD)",
                "Declared Tax: 1,000",
                "Tax Adjustment: 250",
                "Assessed Tax: 1,250",
            ],
            [
                "Amended Assessment Notice 2025 (USD)",
                "Assessed Tax: 1,300",
                "Tax Penalty: (50)",
            ],
        ))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["kind"], "tax_audit_pdf")
        self.assertTrue(payload["ready_for_review"])
        self.assertEqual(payload["manifest"]["source_type"], "pdf")
        self.assertEqual(payload["manifest"]["detected_locale"], "en")

        assessed = [fact for fact in payload["facts"] if fact["concept_id"] == "tax_assessed"]
        self.assertEqual({fact["value"] for fact in assessed}, {1250.0, 1300.0})
        self.assertEqual({fact["locations"][0]["page_number"] for fact in assessed}, {1, 2})
        self.assertIn("conflicting_tax_fact_values", {issue["rule_id"] for issue in payload["issues"]})

    def test_reconciliation_difference_is_returned_without_silently_changing_assessment(self):
        response = inspect_pdf(tax_report_pdf([
            "Tax Audit Report 2025 (USD)",
            "Declared Tax: 1,000",
            "Tax Adjustment: 250",
            "Assessed Tax: 1,100",
        ]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        assessed = next(fact for fact in payload["facts"] if fact["concept_id"] == "tax_assessed")
        self.assertEqual(assessed["value"], 1100.0)
        issue = next(issue for issue in payload["issues"] if issue["rule_id"] == "tax_assessment_reconciliation_difference")
        self.assertEqual(issue["severity"], "warning")
        self.assertEqual(len(issue["evidence_locations"]), 3)

    def test_image_only_pdf_is_blocked_for_ocr_or_manual_review(self):
        response = inspect_pdf(tax_report_pdf([]))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["ready_for_review"])
        issue = next(issue for issue in payload["issues"] if issue["rule_id"] == "pdf_requires_ocr")
        self.assertEqual(issue["severity"], "blocking")
        self.assertEqual(payload["facts"], [])

    def test_pdf_does_not_accept_spreadsheet_mapping_overrides(self):
        response = inspect_pdf(
            tax_report_pdf(["Tax Audit Report 2025 (USD)", "Declared Tax: 1,000"]),
            overrides='{"Declared Tax": "tax_declared"}',
        )

        self.assertEqual(response.status_code, 422)
        self.assertIn("mapping overrides", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
