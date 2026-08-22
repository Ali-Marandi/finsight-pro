"""Local-first evidence intake, review, and validation for FinSight Pro."""

from .intake import CANONICAL_CONCEPTS, apply_mapping_review, inspect_statement, propose_mappings
from .tax_report import TaxReportEvidenceResult, extract_tax_report_evidence
from .models import (
    CanonicalFact,
    EvidenceIntakeResult,
    EvidenceLocation,
    EvidenceManifest,
    MappingDecision,
    MappingStatus,
    Severity,
    ValidationIssue,
)

__all__ = [
    "CANONICAL_CONCEPTS",
    "CanonicalFact",
    "EvidenceIntakeResult",
    "EvidenceLocation",
    "EvidenceManifest",
    "MappingDecision",
    "MappingStatus",
    "Severity",
    "ValidationIssue",
    "TaxReportEvidenceResult",
    "extract_tax_report_evidence",
    "apply_mapping_review",
    "inspect_statement",
    "propose_mappings",
]
