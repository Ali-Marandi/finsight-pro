import tempfile
import unittest
from pathlib import Path

from reportlab.pdfgen import canvas

from finsight.evidence import extract_tax_report_evidence


class TaxReportEvidenceTests(unittest.TestCase):
    def _create_tax_report(self, rows: list[str]) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "tax_audit_2025.pdf"
        pdf = canvas.Canvas(str(path))
        y_position = 760
        for row in rows:
            pdf.drawString(72, y_position, row)
            y_position -= 28
        pdf.save()
        return path

    def test_extracts_tax_facts_with_page_level_provenance(self):
        report = self._create_tax_report([
            "Tax Audit Report 2025 (USD)",
            "Declared Tax: 1,000",
            "Tax Adjustment: 250",
            "Assessed Tax: 1,250",
            "Tax Penalty: (50)",
        ])

        result = extract_tax_report_evidence(report)
        facts = {fact.concept_id: fact for fact in result.facts}

        self.assertTrue(result.is_ready_for_review)
        self.assertEqual(result.manifest.source_type, "pdf")
        self.assertEqual(facts["tax_declared"].value, 1000.0)
        self.assertEqual(facts["tax_adjustment"].value, 250.0)
        self.assertEqual(facts["tax_assessed"].value, 1250.0)
        self.assertEqual(facts["tax_penalty"].value, -50.0)
        self.assertEqual(facts["tax_assessed"].period, "2025")
        self.assertEqual(facts["tax_assessed"].locations[0].page_number, 1)
        self.assertEqual(facts["tax_assessed"].locations[0].sheet_name, "PDF")

    def test_marks_reconciliation_difference_for_reviewer(self):
        report = self._create_tax_report([
            "Tax Audit Report 2025 (USD)",
            "Declared Tax: 1,000",
            "Tax Adjustment: 250",
            "Assessed Tax: 1,100",
        ])

        result = extract_tax_report_evidence(report)

        self.assertIn("tax_assessment_reconciliation_difference", {issue.rule_id for issue in result.issues})


if __name__ == "__main__":
    unittest.main()
