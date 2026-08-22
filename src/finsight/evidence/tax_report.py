"""Evidence-grounded extraction for digital tax-audit report PDFs.

The module deliberately produces reviewable proposals, not a tax conclusion. Every
extracted fact retains a page/table/line reference and the caller must route material
items through human review before creating a final workpaper.
"""

from __future__ import annotations

import hashlib
import io
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from .models import (
    CanonicalFact,
    EvidenceLocation,
    EvidenceManifest,
    Severity,
    ValidationIssue,
    ValidationStatus,
    source_type_for,
)

# One small, transparent vocabulary is safer than a broad unreviewed classifier.
TAX_AUDIT_ALIASES: dict[str, tuple[str, ...]] = {
    "tax_declared": ("declared tax", "tax declared", "مالیات ابرازی", "مالیات اظهارشده"),
    "tax_assessed": ("assessed tax", "tax assessment", "final tax", "مالیات تشخیصی", "مالیات قطعی"),
    "tax_adjustment": ("tax adjustment", "adjustment", "adjustments", "تعدیل مالیاتی", "تعدیلات مالیاتی", "تعدیل"),
    "taxable_income": ("taxable income", "assessable income", "درآمد مشمول مالیات", "درآمد مشمول"),
    "tax_payable": ("tax payable", "income tax payable", "مالیات پرداختنی", "مالیات قابل پرداخت"),
    "tax_expense": ("income tax expense", "tax expense", "هزینه مالیات", "مالیات بر درآمد"),
    "tax_credit": ("tax credit", "tax credits", "اعتبار مالیاتی", "اعتبارات مالیاتی"),
    "withholding_tax": ("withholding tax", "tax withheld", "مالیات تکلیفی", "مالیات کسرشده"),
    "vat_payable": ("vat payable", "value added tax", "sales tax payable", "مالیات ارزش افزوده", "مالیات بر ارزش افزوده"),
    "tax_penalty": ("tax penalty", "penalties", "late payment penalty", "جرایم مالیاتی", "جریمه مالیاتی", "جرایم"),
    "late_payment_interest": ("late payment interest", "interest on tax", "late interest", "خسارت تاخیر", "بهره دیرکرد"),
}

_PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_NUMBER_PATTERN = re.compile(r"(?<![\w.])\(?[-+]?\s*[0-9][0-9,٬٫.\s]*\)?(?:\s*[KMBkmb])?(?![\w.])")
_PERIOD_PATTERN = re.compile(r"\b(?:1[34]\d{2}|20\d{2})\b")


@dataclass
class TaxReportEvidenceResult:
    """Reviewable tax-report extraction output independent of any generative model."""

    manifest: EvidenceManifest
    facts: list[CanonicalFact]
    issues: list[ValidationIssue]
    extraction_mode: str

    @property
    def is_ready_for_review(self) -> bool:
        return not any(issue.severity is Severity.BLOCKING and issue.status is ValidationStatus.FAIL for issue in self.issues)

    def to_dict(self) -> dict:
        return {
            "manifest": {**asdict(self.manifest), "imported_at": self.manifest.imported_at.isoformat()},
            "extraction_mode": self.extraction_mode,
            "ready_for_review": self.is_ready_for_review,
            "facts": [
                {
                    "concept_id": fact.concept_id,
                    "value": fact.value,
                    "period": fact.period,
                    "currency": fact.currency,
                    "scale": fact.scale,
                    "locations": [asdict(location) for location in fact.locations],
                }
                for fact in self.facts
            ],
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


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for block in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _normalize(value: str) -> str:
    return " ".join(value.translate(_PERSIAN_DIGITS).replace("ي", "ی").replace("ك", "ک").casefold().split())


def _detect_currency(text: str) -> str | None:
    lowered = _normalize(text)
    if any(token in lowered for token in ("ریال", "rial", "irr")):
        return "IRR"
    if any(token in lowered for token in ("تومان", "toman")):
        return "IRT"
    if any(token in lowered for token in ("usd", "$", "dollar")):
        return "USD"
    return None


def _parse_number(value: str) -> float | None:
    candidate = value.translate(_PERSIAN_DIGITS).strip()
    negative = candidate.startswith("(") and candidate.endswith(")")
    candidate = candidate.strip("()").replace("٬", ",").replace("٫", ".")
    candidate = re.sub(r"[^0-9,\.KMBkmb+-]", "", candidate)
    if not candidate or not re.search(r"\d", candidate):
        return None
    multiplier = 1.0
    if candidate[-1:] in {"K", "k", "M", "m", "B", "b"}:
        suffix = candidate[-1:].upper()
        multiplier = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}[suffix]
        candidate = candidate[:-1]
    candidate = candidate.replace(",", "")
    try:
        parsed = float(candidate) * multiplier
    except ValueError:
        return None
    return -abs(parsed) if negative else parsed


def _concept_for(label: str) -> str | None:
    normalized = _normalize(label)
    matches: list[tuple[int, str]] = []
    for concept, aliases in TAX_AUDIT_ALIASES.items():
        for alias in aliases:
            normalized_alias = _normalize(alias)
            if normalized_alias in normalized or normalized in normalized_alias:
                matches.append((len(normalized_alias), concept))
    return max(matches)[1] if matches else None


def _period_for(text: str) -> str:
    matches = _PERIOD_PATTERN.findall(text.translate(_PERSIAN_DIGITS))
    return matches[0] if matches else "unknown"


def _numeric_candidates(text: str) -> list[float]:
    values: list[float] = []
    for match in _NUMBER_PATTERN.finditer(text.translate(_PERSIAN_DIGITS)):
        parsed = _parse_number(match.group(0))
        if parsed is not None:
            values.append(parsed)
    return values


def _fact(
    concept: str,
    value: float,
    period: str,
    manifest: EvidenceManifest,
    page_number: int,
    column_name: str,
    row_number: int | None = None,
    table_index: int | None = None,
    cell_reference: str | None = None,
    currency: str | None = None,
) -> CanonicalFact:
    return CanonicalFact(
        concept_id=concept,
        value=value,
        period=period,
        currency=currency,
        locations=[EvidenceLocation(
            file_name=manifest.file_name,
            sheet_name="PDF",
            column_name=column_name,
            row_number=row_number,
            page_number=page_number,
            table_index=table_index,
            cell_reference=cell_reference,
        )],
    )


def _extract_from_table(
    table: list[list[str | None]],
    table_index: int,
    page_number: int,
    manifest: EvidenceManifest,
    period: str,
    currency: str | None,
) -> Iterable[CanonicalFact]:
    for row_index, raw_row in enumerate(table, start=1):
        row = [str(cell or "") for cell in raw_row]
        for cell_index, label in enumerate(row):
            concept = _concept_for(label)
            if not concept:
                continue
            numbers = _numeric_candidates(" ".join(row[cell_index + 1:]))
            if not numbers:
                continue
            yield _fact(
                concept=concept,
                value=numbers[-1],
                period=period,
                manifest=manifest,
                page_number=page_number,
                column_name=label,
                row_number=row_index,
                table_index=table_index,
                cell_reference=f"R{row_index}C{cell_index + 1}",
                currency=currency,
            )


def _extract_from_text(
    text: str,
    page_number: int,
    manifest: EvidenceManifest,
    period: str,
    currency: str | None,
) -> Iterable[CanonicalFact]:
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        concept = _concept_for(raw_line)
        if not concept:
            continue
        values = _numeric_candidates(raw_line)
        if not values:
            continue
        yield _fact(
            concept=concept,
            value=values[-1],
            period=period,
            manifest=manifest,
            page_number=page_number,
            column_name=raw_line.strip()[:160],
            row_number=line_number,
            currency=currency,
        )


def _deduplicate(facts: Iterable[CanonicalFact]) -> list[CanonicalFact]:
    """Keep citations for distinct values; remove only exact duplicate extraction paths."""
    retained: list[CanonicalFact] = []
    seen: set[tuple[str, float, int | None, str | None]] = set()
    for fact in facts:
        location = fact.locations[0]
        key = (fact.concept_id, fact.value, location.page_number, location.cell_reference or location.column_name)
        if key not in seen:
            retained.append(fact)
            seen.add(key)
    return retained


def _validation_issues(facts: list[CanonicalFact], manifest: EvidenceManifest) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not facts:
        issues.append(ValidationIssue(
            rule_id="no_tax_audit_facts_extracted",
            severity=Severity.BLOCKING,
            status=ValidationStatus.FAIL,
            message="No recognized tax-audit facts were extracted from this digital PDF.",
            remediation="Use a text-based report with recognizable tax labels, or route this document to OCR/manual review.",
        ))
        return issues

    by_concept: dict[str, list[CanonicalFact]] = {}
    for fact in facts:
        by_concept.setdefault(fact.concept_id, []).append(fact)
    for concept, concept_facts in by_concept.items():
        values = {fact.value for fact in concept_facts}
        if len(values) > 1:
            issues.append(ValidationIssue(
                rule_id="conflicting_tax_fact_values",
                severity=Severity.WARNING,
                status=ValidationStatus.FAIL,
                message=f"Multiple values were extracted for '{concept}'.",
                remediation="Review the cited pages to determine whether the values are comparative periods, components, or a true conflict.",
                evidence_locations=[location for fact in concept_facts for location in fact.locations],
            ))

    declared = by_concept.get("tax_declared", [])
    adjustment = by_concept.get("tax_adjustment", [])
    assessed = by_concept.get("tax_assessed", [])
    if len(declared) == len(adjustment) == len(assessed) == 1:
        expected = declared[0].value + adjustment[0].value
        actual = assessed[0].value
        if abs(expected - actual) > max(1.0, abs(actual) * 0.001):
            issues.append(ValidationIssue(
                rule_id="tax_assessment_reconciliation_difference",
                severity=Severity.WARNING,
                status=ValidationStatus.FAIL,
                message="Declared tax plus extracted adjustment does not reconcile to assessed tax.",
                remediation="Confirm the scope, sign convention, and whether additional adjustments are disclosed elsewhere in the report.",
                evidence_locations=[*declared[0].locations, *adjustment[0].locations, *assessed[0].locations],
            ))
    return issues


def extract_tax_report_evidence(path: str | Path) -> TaxReportEvidenceResult:
    """Compile evidence from a digital tax-audit PDF into reviewable canonical facts.

    This prototype supports text-based PDFs. It deliberately returns a blocking issue
    for documents requiring OCR rather than inventing values from images.
    """
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)
    if source_type_for(source) != "pdf":
        raise ValueError("Tax-report extraction currently supports PDF files only.")

    try:
        import pdfplumber
    except ImportError as exc:
        raise ImportError("pdfplumber is required for tax-report PDF extraction.") from exc

    with pdfplumber.open(io.BytesIO(source.read_bytes())) as pdf:
        page_payloads = [(page.extract_text() or "", page.extract_tables() or []) for page in pdf.pages]

    all_text = "\n".join(text for text, _ in page_payloads)
    manifest = EvidenceManifest(
        file_name=source.name,
        file_hash=_hash_file(source),
        source_type="pdf",
        sheet_name="PDF",
        detected_locale="fa" if any("\u0600" <= character <= "\u06ff" for character in all_text) else "en",
        row_count=sum(len(text.splitlines()) for text, _ in page_payloads),
        column_count=0,
    )
    if not all_text.strip():
        return TaxReportEvidenceResult(
            manifest=manifest,
            facts=[],
            extraction_mode="digital_pdf_only",
            issues=[ValidationIssue(
                rule_id="pdf_requires_ocr",
                severity=Severity.BLOCKING,
                status=ValidationStatus.FAIL,
                message="No embedded text was found; this PDF requires an approved OCR workflow.",
                remediation="Route the document to OCR/manual review. Do not infer financial values from an unreadable image.",
            )],
        )

    period = _period_for(all_text)
    currency = _detect_currency(all_text)
    extracted: list[CanonicalFact] = []
    for page_number, (page_text, tables) in enumerate(page_payloads, start=1):
        for table_index, table in enumerate(tables, start=1):
            extracted.extend(_extract_from_table(table, table_index, page_number, manifest, period, currency))
        extracted.extend(_extract_from_text(page_text, page_number, manifest, period, currency))

    facts = _deduplicate(extracted)
    return TaxReportEvidenceResult(
        manifest=manifest,
        facts=facts,
        issues=_validation_issues(facts, manifest),
        extraction_mode="pdfplumber_tables_and_text",
    )
