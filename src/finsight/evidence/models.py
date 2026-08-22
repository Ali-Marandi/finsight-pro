"""Typed domain models for the local-first Evidence Compiler MVP."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import pandas as pd


class MappingStatus(str, Enum):
    CONFIRMED = "confirmed"
    SUGGESTED = "suggested"
    NEEDS_REVIEW = "needs_review"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    BLOCKING = "blocking"


class ValidationStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class EvidenceLocation:
    """A precise reference to a field or value in the original user file."""

    file_name: str
    sheet_name: str
    column_name: str
    row_number: int | None = None


@dataclass
class MappingDecision:
    """A proposed or confirmed mapping from an input column to a canonical concept."""

    source_column: str
    concept_id: str | None
    confidence: float
    rationale: str
    status: MappingStatus


@dataclass
class CanonicalFact:
    """A normalized financial value with the locations from which it was compiled."""

    concept_id: str
    value: float
    period: str
    locations: list[EvidenceLocation]
    currency: str | None = None
    scale: str | None = None


@dataclass
class ValidationIssue:
    """A deterministic data-quality result with a practical remediation message."""

    rule_id: str
    severity: Severity
    status: ValidationStatus
    message: str
    remediation: str
    evidence_locations: list[EvidenceLocation] = field(default_factory=list)


@dataclass
class EvidenceManifest:
    """Metadata that makes an imported source file identifiable and auditable."""

    file_name: str
    file_hash: str
    source_type: str
    sheet_name: str
    imported_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    detected_locale: str | None = None
    row_count: int = 0
    column_count: int = 0


@dataclass
class EvidenceIntakeResult:
    """The non-destructive result of inspecting a user-provided financial statement."""

    manifest: EvidenceManifest
    frame: pd.DataFrame
    mappings: list[MappingDecision]
    canonical_frame: pd.DataFrame
    facts: list[CanonicalFact]
    issues: list[ValidationIssue]

    @property
    def is_ready_for_analysis(self) -> bool:
        return not any(issue.severity is Severity.BLOCKING and issue.status is ValidationStatus.FAIL for issue in self.issues)

    @property
    def health_summary(self) -> dict[str, int]:
        return {
            severity.value: sum(1 for issue in self.issues if issue.severity is severity and issue.status is ValidationStatus.FAIL)
            for severity in Severity
        }

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe review payload without leaking the in-memory dataframe."""

        return {
            "manifest": {
                **asdict(self.manifest),
                "imported_at": self.manifest.imported_at.isoformat(),
            },
            "mappings": [
                {**asdict(mapping), "status": mapping.status.value}
                for mapping in self.mappings
            ],
            "health": self.health_summary,
            "ready_for_analysis": self.is_ready_for_analysis,
            "issues": [
                {
                    **asdict(issue),
                    "severity": issue.severity.value,
                    "status": issue.status.value,
                    "evidence_locations": [asdict(location) for location in issue.evidence_locations],
                }
                for issue in self.issues
            ],
        }


def source_type_for(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix in {".xlsx", ".xlsm"}:
        return "excel"
    return "unknown"
