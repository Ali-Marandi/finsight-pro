"""Compliance Engine — Checks financial statements against Iranian Accounting Standards and IFRS.
Provides a comprehensive compliance report with severity levels and remediation guidance.
"""

from typing import Optional
import re

# Compliance rules for Iranian Accounting Standards (آیین‌نامه حسابداری)
IRANIAN_STANDARDS = {
    "IAS_1": {
        "name": "IAS 1 — Presentation of Financial Statements",
        "name_fa": "استاندارد ۱ — ارائه صورت‌های مالی",
        "checks": [
            {
                "id": "IAS1_01",
                "rule": "Income statement must include revenue, profit/loss, and comprehensive income",
                "rule_fa": "صورت سود و زیان باید شامل درآمد، سود/زیان و سود جامع باشد",
                "severity": "blocking",
            },
            {
                "id": "IAS1_02",
                "rule": "Balance sheet must balance: Assets = Liabilities + Equity",
                "rule_fa": "ترازنامه باید تراز باشد: دارایی = بدهی + حقوق صاحبان سهام",
                "severity": "blocking",
            },
        ],
    },
    "IAS_2": {
        "name": "IAS 2 — Inventories",
        "name_fa": "استاندارد ۲ — موجودی‌ها",
        "checks": [
            {
                "id": "IAS2_01",
                "rule": "Inventory must be valued at lower of cost or net realizable value",
                "rule_fa": "موجودی باید به کمترینِ بهای تمام‌شده یا ارزش خالص قابل‌تحقق ارزیابی شود",
                "severity": "warning",
            },
        ],
    },
    "IAS_7": {
        "name": "IAS 7 — Statement of Cash Flows",
        "name_fa": "استاندارد ۷ — صورت جریان وجوه نقد",
        "checks": [
            {
                "id": "IAS7_01",
                "rule": "Cash flow statement must classify activities as operating, investing, or financing",
                "rule_fa": "صورت جریان نقد باید فعالیت‌ها را به عملیاتی، سرمایه‌گذاری و تأمین مالی طبقه‌بندی کند",
                "severity": "info",
            },
        ],
    },
    "IAS_16": {
        "name": "IAS 16 — Property, Plant & Equipment",
        "name_fa": "استاندارد ۱۶ — دارایی‌های ثابت",
        "checks": [
            {
                "id": "IAS16_01",
                "rule": "Fixed assets must be depreciated systematically over useful life",
                "rule_fa": "دارایی‌های ثابت باید به‌صورت سیستماتیک طی عمر مفید استهلاک شوند",
                "severity": "warning",
            },
        ],
    },
    "IAS_36": {
        "name": "IAS 36 — Impairment of Assets",
        "name_fa": "استاندارد ۳۶ — کاهش ارزش دارایی‌ها",
        "checks": [
            {
                "id": "IAS36_01",
                "rule": "Impairment testing required when indicators of impairment exist",
                "rule_fa": "آزمون کاهش ارزش در صورت وجود نشانه‌های کاهش ارزش الزامی است",
                "severity": "warning",
            },
        ],
    },
    "IFRS_9": {
        "name": "IFRS 9 — Financial Instruments",
        "name_fa": "IFRS ۹ — ابزارهای مالی",
        "checks": [
            {
                "id": "IFRS9_01",
                "rule": "Financial assets must be classified as amortized cost, FVOCI, or FVTPL",
                "rule_fa": "دارایی‌های مالی باید به‌عنوان بهای تمام‌شده، ارزش منصفانه از طریق سایر سود و زیان یا ارزش منصفانه از طریق سود و زیان طبقه‌بندی شوند",
                "severity": "info",
            },
        ],
    },
    "IFRS_15": {
        "name": "IFRS 15 — Revenue from Contracts",
        "name_fa": "IFRS ۱۵ — درآمد از قراردادها",
        "checks": [
            {
                "id": "IFRS15_01",
                "rule": "Revenue must be recognized using the 5-step model",
                "rule_fa": "درآمد باید با استفاده از مدل ۵ مرحله‌ای شناسایی شود",
                "severity": "info",
            },
        ],
    },
    "IFRS_16": {
        "name": "IFRS 16 — Leases",
        "name_fa": "IFRS ۱۶ — اجاره‌ها",
        "checks": [
            {
                "id": "IFRS16_01",
                "rule": "Lessee must recognize right-of-use asset and lease liability",
                "rule_fa": "اجاره‌کننده باید دارایی حق استفاده و بدهی اجاره را شناسایی کند",
                "severity": "info",
            },
        ],
    },
}

# Iranian-specific compliance checks
IRAN_SPECIFIC_CHECKS = [
    {
        "id": "IR_VAT_01",
        "standard": "Iran VAT Law",
        "standard_fa": "قانون مالیات بر ارزش افزوده ایران",
        "rule": "VAT (9%) must be separately stated in sales invoices",
        "rule_fa": "مالیات بر ارزش افزوده (۹٪) باید جداگانه در فاکتورهای فروش ذکر شود",
        "severity": "warning",
    },
    {
        "id": "IR_TAX_01",
        "standard": "Iran Income Tax",
        "standard_fa": "مالیات بر درآمد ایران",
        "rule": "Corporate tax rate is 25% of taxable income (22.5% for TSE-listed companies)",
        "rule_fa": "نرخ مالیات شرکتی ۲۵٪ درآمد مشمول مالیات است (۲۲.۵٪ برای شرکت‌های بورسی)",
        "severity": "warning",
    },
    {
        "id": "IR_AUDIT_01",
        "standard": "Iran Audit Organization",
        "standard_fa": "سازمان حسابرسی ایران",
        "rule": "Statutory audit required for companies exceeding 50B Rial in revenue",
        "rule_fa": "حسابرسی قانونی برای شرکت‌های بالای ۵۰ میلیارد ریال درآمد الزامی است",
        "severity": "info",
    },
    {
        "id": "IR_SOCIAL_01",
        "standard": "Iran Social Security",
        "standard_fa": "سازمان تأمین اجتماعی ایران",
        "rule": "Social security contributions: 23% employer + 7% employee of gross salary",
        "rule_fa": "حقوق تأمین اجتماعی: ۲۳٪ کارفرما + ۷٪ کارگر از حقوق ناخالص",
        "severity": "info",
    },
]


def run_compliance_check(financial_data: dict) -> dict:
    """Run compliance checks against Iranian standards and IFRS.

    Args:
        financial_data: Dict with extracted financial figures (revenue, total_assets, etc.)

    Returns:
        Compliance report with passed/failed checks, overall score, and recommendations
    """
    results = []
    passed = 0
    failed = 0
    na = 0
    critical_issues = []
    warnings = []
    info_items = []

    # Run standard checks
    for std_code, std in IRANIAN_STANDARDS.items():
        for check in std["checks"]:
            result = _evaluate_check(check, financial_data)
            results.append({
                "standard": std["name"],
                "standard_fa": std["name_fa"],
                "check_id": check["id"],
                "rule": check["rule"],
                "rule_fa": check["rule_fa"],
                "severity": check["severity"],
                **result,
            })
            if result["status"] == "pass":
                passed += 1
            elif result["status"] == "fail":
                failed += 1
                if check["severity"] == "blocking":
                    critical_issues.append(result["message"])
                elif check["severity"] == "warning":
                    warnings.append(result["message"])
            else:
                na += 1

    # Run Iran-specific checks
    for check in IRAN_SPECIFIC_CHECKS:
        result = _evaluate_iran_check(check, financial_data)
        results.append({
            "standard": check["standard"],
            "standard_fa": check["standard_fa"],
            "check_id": check["id"],
            "rule": check["rule"],
            "rule_fa": check["rule_fa"],
            "severity": check["severity"],
            **result,
        })
        if result["status"] == "pass":
            passed += 1
        elif result["status"] == "fail":
            failed += 1
            if check["severity"] == "warning":
                warnings.append(result["message"])
        else:
            na += 1
            info_items.append(result["message"])

    total = passed + failed
    compliance_score = round((passed / total * 100)) if total > 0 else 0

    return {
        "compliance_score": compliance_score,
        "total_checks": len(results),
        "passed": passed,
        "failed": failed,
        "not_applicable": na,
        "critical_issues": critical_issues,
        "warnings": warnings,
        "info_items": info_items,
        "status": "compliant" if compliance_score >= 80 else ("needs_attention" if compliance_score >= 50 else "non_compliant"),
        "results": results,
        "recommendations": _generate_compliance_recommendations(results, financial_data),
    }


def _evaluate_check(check: dict, fd: dict) -> dict:
    """Evaluate a single compliance check against financial data."""
    check_id = check["id"]

    # IAS1_02: Balance sheet balance
    if check_id == "IAS1_02":
        assets = fd.get("total_assets", 0)
        liabilities = fd.get("total_liabilities", 0)
        equity = fd.get("total_equity", 0)
        if assets > 0 and (liabilities + equity) > 0:
            diff_pct = abs(assets - (liabilities + equity)) / max(assets, 1) * 100
            if diff_pct <= 5:
                return {"status": "pass", "message": "Balance sheet balances within 5% tolerance"}
            else:
                return {
                    "status": "fail",
                    "message": f"Balance sheet doesn't balance: Assets={assets:,.0f}, L+E={liabilities + equity:,.0f} ({diff_pct:.1f}% diff)",
                    "remediation": "Verify all balance sheet items are correctly extracted and classified",
                }
        return {"status": "not_applicable", "message": "Insufficient data to verify balance sheet equation"}

    # IAS2_01: Inventory valuation check
    if check_id == "IAS2_01":
        inventory = fd.get("inventory", 0)
        revenue = fd.get("revenue", 0)
        if inventory > 0 and revenue > 0:
            inv_ratio = inventory / revenue
            if inv_ratio < 0.50:
                return {"status": "pass", "message": f"Inventory to revenue ratio ({inv_ratio:.1%}) is reasonable"}
            else:
                return {
                    "status": "fail",
                    "message": f"Inventory/revenue ratio ({inv_ratio:.1%}) is high — possible overvaluation or slow-moving stock",
                    "remediation": "Review inventory valuation method and consider impairment testing per IAS 36",
                }
        return {"status": "not_applicable", "message": "No inventory data available"}

    # Default: check if we have the minimum data
    required_fields = ["revenue", "net_income", "total_assets"]
    if any(fd.get(f, 0) > 0 for f in required_fields):
        return {
            "status": "not_applicable",
            "message": "Requires manual review — this check cannot be automatically verified from the available data",
            "remediation": "Have a qualified auditor review this item",
        }
    return {"status": "not_applicable", "message": "Insufficient financial data to evaluate"}


def _evaluate_iran_check(check: dict, fd: dict) -> dict:
    """Evaluate Iran-specific compliance check."""
    check_id = check["id"]

    # IR_TAX_01: Tax rate check
    if check_id == "IR_TAX_01":
        tax = fd.get("tax_expense", 0)
        ebt = fd.get("ebit", 0)
        if ebt > 0 and tax > 0:
            effective_rate = tax / ebt
            if 0.15 <= effective_rate <= 0.30:
                return {"status": "pass", "message": f"Effective tax rate ({effective_rate:.1%}) is within normal range (15-30%)"}
            elif effective_rate > 0.30:
                return {
                    "status": "fail",
                    "message": f"Effective tax rate ({effective_rate:.1%}) exceeds 30% — verify tax calculations",
                    "remediation": "Review tax provisions and consult with tax advisor",
                }
            else:
                return {"status": "pass", "message": f"Effective tax rate ({effective_rate:.1%}) is below 25% — possible tax incentives"}
        return {"status": "not_applicable", "message": "No tax data available for verification"}

    # IR_VAT_01
    if check_id == "IR_VAT_01":
        return {
            "status": "not_applicable",
            "message": "VAT compliance requires invoice-level data not available in summary statements",
            "remediation": "Ensure all sales invoices include separate 9% VAT line items",
        }

    # Default
    return {
        "status": "not_applicable",
        "message": "Requires manual review with supporting documentation",
        "remediation": "Consult with an Iranian audit firm for detailed compliance assessment",
    }


def _generate_compliance_recommendations(results: list[dict], fd: dict) -> list[dict]:
    """Generate prioritized compliance recommendations."""
    recs = []

    # Financial health red flags
    if fd.get("current_ratio", 2) < 1:
        recs.append({
            "priority": "high",
            "title": "Liquidity Crisis Risk",
            "title_fa": "خطر بحران نقدینگی",
            "description": "Current ratio below 1.0 indicates potential inability to meet short-term obligations. This is a significant compliance concern under Iranian commercial law.",
        })

    if fd.get("debt_to_equity", 0) > 3:
        recs.append({
            "priority": "high",
            "title": "Excessive Leverage",
            "title_fa": "اهرم مالی بیش از حد",
            "description": "Debt-to-equity ratio exceeds 3.0, which may trigger enhanced disclosure requirements under Iranian Stock Exchange regulations.",
        })

    # IFRS recommendations
    failed_checks = [r for r in results if r.get("status") == "fail"]
    for fc in failed_checks:
        if fc.get("severity") == "blocking":
            recs.append({
                "priority": "critical",
                "title": f"Non-Compliance: {fc['check_id']}",
                "title_fa": f"عدم انطباق: {fc['check_id']}",
                "description": fc.get("message", "") + (" " + fc.get("remediation", "") if fc.get("remediation") else ""),
            })

    # General recommendation
    if fd.get("revenue", 0) > 0:
        recs.append({
            "priority": "medium",
            "title": "Annual Audit Recommendation",
            "title_fa": "پیشنهاد حسابرسی سالانه",
            "description": "For companies with significant revenue, engaging a certified Iranian audit firm is recommended to ensure full compliance with Iranian Accounting Standards and IFRS.",
        })

    return recs[:8]  # Top 8


def get_compliance_standards() -> list[dict]:
    """Return list of all compliance standards and their checks."""
    standards = []
    for code, std in IRANIAN_STANDARDS.items():
        standards.append({
            "code": code,
            "name": std["name"],
            "name_fa": std["name_fa"],
            "check_count": len(std["checks"]),
        })
    for check in IRAN_SPECIFIC_CHECKS:
        standards.append({
            "code": check["id"],
            "name": check["standard"],
            "name_fa": check["standard_fa"],
            "check_count": 1,
        })
    return standards
