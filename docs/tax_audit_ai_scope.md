# FinSight Evidence — Scope for Tax-Audit Intelligence

## Product boundary

FinSight should assist tax professionals in reviewing evidence and preparing auditable work products. It must **not** issue a tax filing position, certify compliance, calculate a taxpayer’s liability as an authoritative conclusion, or replace the judgment and sign-off of a licensed professional. Its output is a reviewed, evidence-linked draft for a human tax or audit reviewer.

## Primary workflows

| Workflow | User question | Required system output |
|---|---|---|
| Intake and classification | What documents, periods, entities, and jurisdictions are present? | Immutable manifest, document classification, language/format detection, and missing-evidence list. |
| Evidence extraction | What claims, figures, adjustments, and citations appear in the report? | Structured facts with page/paragraph/table-cell citations and extraction confidence. |
| Reconciliation | Do report figures align with statements, ledgers, and prior-period evidence? | Deterministic reconciliation results, material differences, and source links. |
| Tax-risk review | Which reported assertions require human investigation? | Ranked review queue with policy/rule reference, evidence, confidence, and an explicit abstain state. |
| Workpaper composition | Can a reviewer defend the conclusion later? | Versioned Decision Proof with reviewer actions, unresolved items, and exportable audit trail. |

## Trust boundary

A model may classify, extract, cluster, compare, retrieve authoritative policy text, and draft a review note. It may not silently modify a financial fact, infer a missing tax position as a fact, or produce a final conclusion when required evidence is absent. Every machine-produced claim must be labeled as **confirmed calculation**, **review hypothesis**, or **unknown**.

## Initial measurable outcomes

| Outcome | Product metric | Quality guardrail |
|---|---|---|
| Faster evidence intake | Time from file selection to reviewable manifest | No source document or extracted fact is dropped without a visible exception. |
| Better extraction | Field-level precision/recall on a blinded gold set | A low-confidence field cannot be presented as confirmed. |
| More reliable reconciliation | Rate of material mismatch detection | Deterministic accounting controls always run before generative summaries. |
| Reviewer efficiency | Time from report intake to reviewer-ready workpaper | Human reviewer remains required for any blocking or material item. |
| Defensible output | Share of claims with a usable source citation | No policy or AI claim is exportable without evidence/provenance. |
