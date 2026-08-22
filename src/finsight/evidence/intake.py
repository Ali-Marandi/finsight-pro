"""Non-destructive financial-file intake for the Evidence Compiler MVP."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path

import pandas as pd

from .models import (
    CanonicalFact,
    EvidenceIntakeResult,
    EvidenceLocation,
    EvidenceManifest,
    MappingDecision,
    MappingStatus,
    source_type_for,
)
from .validation import validate_canonical_frame, validate_mapping_decisions

CANONICAL_CONCEPTS = (
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
)

# The dictionary is deliberately small and review-first. A suggestion is never silently applied.
ALIASES: dict[str, tuple[str, ...]] = {
    "period": ("year", "quarter", "fiscal_period", "reporting_period", "دوره", "سال", "فصل"),
    "revenue": ("sales", "turnover", "net_sales", "درآمد", "فروش", "فروش_خالص"),
    "gross_profit": ("gross_income", "سود_ناخالص"),
    "operating_income": ("operating_profit", "ebit", "سود_عملیاتی", "درآمد_عملیاتی"),
    "net_income": ("net_profit", "profit_after_tax", "سود_خالص", "سود_پس_از_مالیات"),
    "total_assets": ("assets", "دارایی", "دارایی_کل"),
    "current_assets": ("short_term_assets", "دارایی_جاری"),
    "inventory": ("stock", "موجودی", "موجودی_کالا"),
    "cash": ("cash_and_equivalents", "وجه_نقد", "نقد"),
    "total_liabilities": ("liabilities", "بدهی", "بدهی_کل"),
    "current_liabilities": ("short_term_liabilities", "بدهی_جاری"),
    "equity": ("shareholders_equity", "owners_equity", "حقوق_صاحبان_سهام", "حقوق_مالکانه"),
    "operating_cash_flow": ("cash_flow_from_operations", "ocf", "جریان_نقد_عملیاتی"),
    "interest_expense": ("finance_cost", "interest_cost", "هزینه_بهره", "هزینه_مالی"),
    "cost_of_goods_sold": ("cogs", "cost_of_sales", "بهای_تمام_شده", "بهای_تمام_شده_کالای_فروش_رفته"),
    "accounts_receivable": ("receivables", "trade_receivables", "حساب_های_دریافتنی", "حسابهای_دریافتنی"),
}


def normalize_label(value: object) -> str:
    """Normalize English and Persian-like headers for deterministic dictionary matching."""

    text = unicodedata.normalize("NFKC", str(value)).strip().casefold()
    text = text.replace("ي", "ی").replace("ك", "ک")
    text = re.sub(r"[^\w]+", "_", text, flags=re.UNICODE)
    return re.sub(r"_+", "_", text).strip("_")


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _detected_locale(columns: list[object]) -> str:
    header_text = " ".join(str(column) for column in columns)
    return "fa" if any("\u0600" <= char <= "\u06ff" for char in header_text) else "en"


def _read_frame(path: Path, sheet_name: str | int = 0) -> tuple[pd.DataFrame, str]:
    source_type = source_type_for(path)
    if source_type == "csv":
        return pd.read_csv(path), "CSV"
    if source_type == "excel":
        workbook = pd.ExcelFile(path, engine="openpyxl")
        selected_name = workbook.sheet_names[sheet_name] if isinstance(sheet_name, int) else sheet_name
        return pd.read_excel(workbook, sheet_name=selected_name), str(selected_name)
    raise ValueError("supported formats are .csv, .xlsx and .xlsm")


def propose_mappings(columns: list[object]) -> list[MappingDecision]:
    """Produce explicit mapping proposals; only canonical exact matches are confirmed."""

    alias_index = {
        normalize_label(alias): concept
        for concept, aliases in ALIASES.items()
        for alias in aliases
    }
    decisions: list[MappingDecision] = []
    for raw_column in columns:
        normalized = normalize_label(raw_column)
        if normalized in CANONICAL_CONCEPTS:
            decisions.append(MappingDecision(
                source_column=str(raw_column),
                concept_id=normalized,
                confidence=1.0,
                rationale="The source header exactly matches the canonical financial concept.",
                status=MappingStatus.CONFIRMED,
            ))
        elif normalized in alias_index:
            decisions.append(MappingDecision(
                source_column=str(raw_column),
                concept_id=alias_index[normalized],
                confidence=0.92,
                rationale=f"The normalized header matches the local alias '{normalized}'.",
                status=MappingStatus.SUGGESTED,
            ))
        else:
            decisions.append(MappingDecision(
                source_column=str(raw_column),
                concept_id=None,
                confidence=0.0,
                rationale="No deterministic canonical or local-alias match was found.",
                status=MappingStatus.NEEDS_REVIEW,
            ))
    return decisions


def apply_mapping_review(
    mappings: list[MappingDecision],
    overrides: dict[str, str | None],
) -> list[MappingDecision]:
    """Apply explicit reviewer decisions without changing the original source file."""

    reviewed: list[MappingDecision] = []
    for mapping in mappings:
        if mapping.source_column not in overrides:
            reviewed.append(mapping)
            continue

        concept = overrides[mapping.source_column]
        if concept is not None and concept not in CANONICAL_CONCEPTS:
            raise ValueError(f"unknown canonical concept: {concept}")
        if concept is None:
            reviewed.append(MappingDecision(
                source_column=mapping.source_column,
                concept_id=None,
                confidence=1.0,
                rationale="The reviewer marked this source column as out of scope for the current canonical model.",
                status=MappingStatus.NEEDS_REVIEW,
            ))
        else:
            reviewed.append(MappingDecision(
                source_column=mapping.source_column,
                concept_id=concept,
                confidence=1.0,
                rationale="The reviewer explicitly confirmed this mapping.",
                status=MappingStatus.CONFIRMED,
            ))
    return reviewed


def _canonical_frame(frame: pd.DataFrame, mappings: list[MappingDecision]) -> pd.DataFrame:
    confirmed: dict[str, str] = {}
    for mapping in mappings:
        if mapping.status in {MappingStatus.CONFIRMED, MappingStatus.SUGGESTED} and mapping.concept_id:
            confirmed.setdefault(mapping.concept_id, mapping.source_column)

    canonical = pd.DataFrame(index=frame.index)
    for concept, source_column in confirmed.items():
        canonical[concept] = frame[source_column]
    if "period" in canonical.columns:
        canonical["period"] = canonical["period"].astype(str).str.strip()
    for concept in canonical.columns:
        if concept != "period":
            canonical[concept] = pd.to_numeric(canonical[concept], errors="coerce")
    return canonical


def _canonical_facts(canonical: pd.DataFrame, manifest: EvidenceManifest, mappings: list[MappingDecision]) -> list[CanonicalFact]:
    source_for_concept = {
        mapping.concept_id: mapping.source_column
        for mapping in mappings
        if mapping.concept_id and mapping.status in {MappingStatus.CONFIRMED, MappingStatus.SUGGESTED}
    }
    if "period" not in canonical.columns:
        return []

    facts: list[CanonicalFact] = []
    for row_index, row in canonical.iterrows():
        period = str(row["period"])
        for concept in canonical.columns:
            if concept == "period" or pd.isna(row[concept]):
                continue
            facts.append(CanonicalFact(
                concept_id=concept,
                value=float(row[concept]),
                period=period,
                locations=[EvidenceLocation(
                    file_name=manifest.file_name,
                    sheet_name=manifest.sheet_name,
                    column_name=source_for_concept.get(concept, concept),
                    row_number=int(row_index) + 2,
                )],
            ))
    return facts


def inspect_statement(
    path: str | Path,
    sheet_name: str | int = 0,
    mapping_overrides: dict[str, str | None] | None = None,
) -> EvidenceIntakeResult:
    """Inspect and compile a source file into reviewable evidence without overwriting it."""

    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)

    frame, selected_sheet = _read_frame(source, sheet_name)
    manifest = EvidenceManifest(
        file_name=source.name,
        file_hash=_file_hash(source),
        source_type=source_type_for(source),
        sheet_name=selected_sheet,
        detected_locale=_detected_locale(frame.columns.tolist()),
        row_count=len(frame),
        column_count=len(frame.columns),
    )
    mappings = propose_mappings(frame.columns.tolist())
    if mapping_overrides:
        mappings = apply_mapping_review(mappings, mapping_overrides)
    canonical = _canonical_frame(frame, mappings)
    issues = [*validate_mapping_decisions(mappings, manifest), *validate_canonical_frame(canonical, manifest)]

    return EvidenceIntakeResult(
        manifest=manifest,
        frame=frame,
        mappings=mappings,
        canonical_frame=canonical,
        facts=_canonical_facts(canonical, manifest, mappings),
        issues=issues,
    )
