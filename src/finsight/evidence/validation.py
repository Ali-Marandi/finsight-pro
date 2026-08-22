"""Deterministic evidence-health rules for the Evidence Compiler MVP."""

from __future__ import annotations

from collections import Counter
import math

import pandas as pd

from .models import (
    EvidenceLocation,
    EvidenceManifest,
    MappingDecision,
    MappingStatus,
    Severity,
    ValidationIssue,
    ValidationStatus,
)

REQUIRED_CONCEPTS = {
    "period",
    "revenue",
    "gross_profit",
    "operating_income",
    "net_income",
    "total_assets",
    "current_assets",
    "inventory",
    "cash",
    "total_liabilities",
    "current_liabilities",
    "equity",
    "operating_cash_flow",
    "interest_expense",
    "cost_of_goods_sold",
    "accounts_receivable",
}


def _location(manifest: EvidenceManifest, column: str, row: int | None = None) -> EvidenceLocation:
    return EvidenceLocation(
        file_name=manifest.file_name,
        sheet_name=manifest.sheet_name,
        column_name=column,
        row_number=row,
    )


def validate_mapping_decisions(mappings: list[MappingDecision], manifest: EvidenceManifest) -> list[ValidationIssue]:
    """Validate whether a reviewer can safely proceed from a proposed mapping."""

    mapped = [mapping for mapping in mappings if mapping.concept_id]
    mapped_concepts = {mapping.concept_id for mapping in mapped}
    issues: list[ValidationIssue] = []

    missing = sorted(REQUIRED_CONCEPTS - mapped_concepts)
    if missing:
        issues.append(ValidationIssue(
            rule_id="missing_required_concepts",
            severity=Severity.BLOCKING,
            status=ValidationStatus.FAIL,
            message=f"The source cannot be compiled because required concepts are missing: {', '.join(missing)}.",
            remediation="Map source columns to each missing concept or provide a statement export that includes them.",
        ))

    counts = Counter(mapping.concept_id for mapping in mapped)
    duplicates = sorted(concept for concept, count in counts.items() if count > 1)
    if duplicates:
        duplicate_locations = [
            _location(manifest, mapping.source_column)
            for mapping in mapped
            if mapping.concept_id in duplicates
        ]
        issues.append(ValidationIssue(
            rule_id="duplicate_concept_mapping",
            severity=Severity.BLOCKING,
            status=ValidationStatus.FAIL,
            message=f"More than one source column maps to: {', '.join(duplicates)}.",
            remediation="Choose one source column per canonical concept before analysis.",
            evidence_locations=duplicate_locations,
        ))

    suggested = [mapping for mapping in mapped if mapping.status is MappingStatus.SUGGESTED]
    if suggested:
        issues.append(ValidationIssue(
            rule_id="mapping_review_required",
            severity=Severity.BLOCKING,
            status=ValidationStatus.FAIL,
            message="One or more mappings are suggestions and require human confirmation.",
            remediation="Review each suggested mapping, then mark it confirmed before generating analysis.",
            evidence_locations=[_location(manifest, mapping.source_column) for mapping in suggested],
        ))

    unmapped = [mapping for mapping in mappings if mapping.status is MappingStatus.NEEDS_REVIEW]
    if unmapped:
        issues.append(ValidationIssue(
            rule_id="unmapped_source_columns",
            severity=Severity.INFO,
            status=ValidationStatus.FAIL,
            message=f"{len(unmapped)} source column(s) are not used by the current canonical financial model.",
            remediation="Ignore non-financial columns or map them explicitly in a future model extension.",
            evidence_locations=[_location(manifest, mapping.source_column) for mapping in unmapped],
        ))

    return issues


def validate_canonical_frame(frame: pd.DataFrame, manifest: EvidenceManifest) -> list[ValidationIssue]:
    """Run deterministic structural and accounting-integrity controls."""

    issues: list[ValidationIssue] = []
    if frame.empty:
        issues.append(ValidationIssue(
            rule_id="empty_statement",
            severity=Severity.BLOCKING,
            status=ValidationStatus.FAIL,
            message="The source file does not contain any data rows.",
            remediation="Provide at least one complete reporting period.",
        ))
        return issues

    if "period" in frame.columns:
        empty_periods = frame["period"].isna() | frame["period"].eq("") | frame["period"].eq("nan")
        if empty_periods.any():
            issues.append(ValidationIssue(
                rule_id="missing_period",
                severity=Severity.BLOCKING,
                status=ValidationStatus.FAIL,
                message="One or more rows have no reporting period.",
                remediation="Enter one unique period label for every financial-statement row.",
                evidence_locations=[_location(manifest, "period", int(index) + 2) for index in frame.index[empty_periods]],
            ))
        duplicates = frame["period"].duplicated(keep=False)
        if duplicates.any():
            issues.append(ValidationIssue(
                rule_id="duplicate_period",
                severity=Severity.BLOCKING,
                status=ValidationStatus.FAIL,
                message="Period labels must be unique within one imported statement.",
                remediation="Separate duplicate periods or correct the source labels before analysis.",
                evidence_locations=[_location(manifest, "period", int(index) + 2) for index in frame.index[duplicates]],
            ))

    numeric_columns = [column for column in frame.columns if column != "period"]
    for column in numeric_columns:
        invalid_rows = frame[column].isna()
        if invalid_rows.any():
            issues.append(ValidationIssue(
                rule_id=f"invalid_numeric_{column}",
                severity=Severity.BLOCKING,
                status=ValidationStatus.FAIL,
                message=f"'{column}' contains empty or non-numeric values.",
                remediation="Correct the affected values, or exclude the incomplete period from this analysis.",
                evidence_locations=[_location(manifest, column, int(index) + 2) for index in frame.index[invalid_rows]],
            ))

    balance_columns = {"total_assets", "total_liabilities", "equity"}
    if balance_columns.issubset(frame.columns):
        for index, row in frame.iterrows():
            assets = row["total_assets"]
            liabilities_plus_equity = row["total_liabilities"] + row["equity"]
            if pd.notna(assets) and pd.notna(liabilities_plus_equity) and not math.isclose(
                float(assets), float(liabilities_plus_equity), rel_tol=0.001, abs_tol=0.01
            ):
                issues.append(ValidationIssue(
                    rule_id="balance_sheet_not_balanced",
                    severity=Severity.BLOCKING,
                    status=ValidationStatus.FAIL,
                    message=(
                        f"Balance sheet does not balance for period '{row.get('period', index)}': "
                        f"assets={assets:g}, liabilities+equity={liabilities_plus_equity:g}."
                    ),
                    remediation="Confirm the units, signs, and source values before approving this statement.",
                    evidence_locations=[
                        _location(manifest, "total_assets", int(index) + 2),
                        _location(manifest, "total_liabilities", int(index) + 2),
                        _location(manifest, "equity", int(index) + 2),
                    ],
                ))

    if {"revenue", "operating_income", "net_income"}.issubset(frame.columns):
        zero_revenue = frame["revenue"].eq(0)
        income_present = frame["operating_income"].ne(0) | frame["net_income"].ne(0)
        suspicious = zero_revenue & income_present
        if suspicious.any():
            issues.append(ValidationIssue(
                rule_id="zero_revenue_with_income",
                severity=Severity.WARNING,
                status=ValidationStatus.FAIL,
                message="One or more periods report zero revenue with non-zero operating or net income.",
                remediation="Confirm whether this is a legitimate non-operating period or a mapping/sign issue.",
                evidence_locations=[_location(manifest, "revenue", int(index) + 2) for index in frame.index[suspicious]],
            ))

    return issues
