"""
Industry Benchmarking Service — Compare a company's ratios against industry peers.
Includes built-in Iranian and global industry benchmarks.
"""

# Industry benchmark data (medians for key ratios)
# Sources: Iranian Stock Exchange data, global industry standards

INDUSTRY_BENCHMARKS = {
    "technology": {
        "name_en": "Technology & Software",
        "name_fa": "فناوری و نرم‌افزار",
        "ratios": {
            "gross_profit_margin": {"median": 0.55, "p25": 0.40, "p75": 0.70},
            "net_profit_margin": {"median": 0.15, "p25": 0.05, "p75": 0.25},
            "return_on_assets": {"median": 0.12, "p25": 0.05, "p75": 0.20},
            "return_on_equity": {"median": 0.18, "p25": 0.08, "p75": 0.30},
            "current_ratio": {"median": 2.5, "p25": 1.5, "p75": 4.0},
            "quick_ratio": {"median": 2.0, "p25": 1.2, "p75": 3.5},
            "debt_to_equity": {"median": 0.4, "p25": 0.1, "p75": 0.8},
            "debt_to_assets": {"median": 0.25, "p25": 0.10, "p75": 0.45},
            "asset_turnover": {"median": 0.8, "p25": 0.4, "p75": 1.3},
            "inventory_turnover": {"median": 8.0, "p25": 4.0, "p75": 15.0},
            "receivables_turnover": {"median": 6.0, "p25": 4.0, "p75": 10.0},
        }
    },
    "manufacturing": {
        "name_en": "Manufacturing & Industrial",
        "name_fa": "تولید و صنعت",
        "ratios": {
            "gross_profit_margin": {"median": 0.30, "p25": 0.20, "p75": 0.40},
            "net_profit_margin": {"median": 0.06, "p25": 0.02, "p75": 0.12},
            "return_on_assets": {"median": 0.06, "p25": 0.02, "p75": 0.10},
            "return_on_equity": {"median": 0.12, "p25": 0.05, "p75": 0.20},
            "current_ratio": {"median": 1.8, "p25": 1.2, "p75": 2.5},
            "quick_ratio": {"median": 1.0, "p25": 0.6, "p75": 1.8},
            "debt_to_equity": {"median": 0.8, "p25": 0.3, "p75": 1.5},
            "debt_to_assets": {"median": 0.40, "p25": 0.25, "p75": 0.55},
            "asset_turnover": {"median": 1.0, "p25": 0.6, "p75": 1.5},
            "inventory_turnover": {"median": 5.0, "p25": 3.0, "p75": 8.0},
            "receivables_turnover": {"median": 7.0, "p25": 4.0, "p75": 12.0},
        }
    },
    "retail": {
        "name_en": "Retail & Commerce",
        "name_fa": "خرده‌فروشی و بازرگانی",
        "ratios": {
            "gross_profit_margin": {"median": 0.25, "p25": 0.15, "p75": 0.35},
            "net_profit_margin": {"median": 0.04, "p25": 0.01, "p75": 0.08},
            "return_on_assets": {"median": 0.05, "p25": 0.02, "p75": 0.09},
            "return_on_equity": {"median": 0.14, "p25": 0.06, "p75": 0.22},
            "current_ratio": {"median": 1.6, "p25": 1.0, "p75": 2.2},
            "quick_ratio": {"median": 0.5, "p25": 0.3, "p75": 0.8},
            "debt_to_equity": {"median": 1.0, "p25": 0.4, "p75": 1.8},
            "debt_to_assets": {"median": 0.45, "p25": 0.30, "p75": 0.60},
            "asset_turnover": {"median": 1.8, "p25": 1.0, "p75": 2.8},
            "inventory_turnover": {"median": 6.0, "p25": 4.0, "p75": 10.0},
            "receivables_turnover": {"median": 10.0, "p25": 6.0, "p75": 16.0},
        }
    },
    "banking": {
        "name_en": "Banking & Finance",
        "name_fa": "بانکداری و مالی",
        "ratios": {
            "gross_profit_margin": {"median": 0.60, "p25": 0.45, "p75": 0.75},
            "net_profit_margin": {"median": 0.18, "p25": 0.10, "p75": 0.28},
            "return_on_assets": {"median": 0.01, "p25": 0.005, "p75": 0.02},
            "return_on_equity": {"median": 0.12, "p25": 0.06, "p75": 0.18},
            "current_ratio": {"median": 1.1, "p25": 1.0, "p75": 1.3},
            "quick_ratio": {"median": 1.0, "p25": 0.9, "p75": 1.2},
            "debt_to_equity": {"median": 8.0, "p25": 5.0, "p75": 12.0},
            "debt_to_assets": {"median": 0.88, "p25": 0.82, "p75": 0.92},
            "asset_turnover": {"median": 0.08, "p25": 0.04, "p75": 0.12},
        }
    },
    "pharmaceutical": {
        "name_en": "Pharmaceutical & Healthcare",
        "name_fa": "دارویی و بهداشتی",
        "ratios": {
            "gross_profit_margin": {"median": 0.50, "p25": 0.35, "p75": 0.65},
            "net_profit_margin": {"median": 0.12, "p25": 0.05, "p75": 0.20},
            "return_on_assets": {"median": 0.10, "p25": 0.04, "p75": 0.16},
            "return_on_equity": {"median": 0.18, "p25": 0.08, "p75": 0.28},
            "current_ratio": {"median": 2.2, "p25": 1.4, "p75": 3.5},
            "quick_ratio": {"median": 1.5, "p25": 0.8, "p75": 2.5},
            "debt_to_equity": {"median": 0.5, "p25": 0.2, "p75": 1.0},
            "debt_to_assets": {"median": 0.30, "p25": 0.15, "p75": 0.50},
            "asset_turnover": {"median": 0.7, "p25": 0.4, "p75": 1.1},
            "inventory_turnover": {"median": 4.0, "p25": 2.5, "p75": 7.0},
        }
    },
    "oil_gas": {
        "name_en": "Oil, Gas & Petrochemical",
        "name_fa": "نفت، گاز و پتروشیمی",
        "ratios": {
            "gross_profit_margin": {"median": 0.35, "p25": 0.20, "p75": 0.50},
            "net_profit_margin": {"median": 0.10, "p25": 0.03, "p75": 0.18},
            "return_on_assets": {"median": 0.07, "p25": 0.02, "p75": 0.12},
            "return_on_equity": {"median": 0.14, "p25": 0.05, "p75": 0.25},
            "current_ratio": {"median": 1.5, "p25": 1.0, "p75": 2.2},
            "quick_ratio": {"median": 0.9, "p25": 0.5, "p75": 1.5},
            "debt_to_equity": {"median": 1.2, "p25": 0.5, "p75": 2.0},
            "debt_to_assets": {"median": 0.50, "p25": 0.35, "p75": 0.65},
            "asset_turnover": {"median": 0.6, "p25": 0.3, "p75": 1.0},
            "inventory_turnover": {"median": 5.0, "p25": 3.0, "p75": 8.0},
        }
    },
    "real_estate": {
        "name_en": "Real Estate & Construction",
        "name_fa": "املاک و مستغلات و ساخت‌وساز",
        "ratios": {
            "gross_profit_margin": {"median": 0.28, "p25": 0.15, "p75": 0.40},
            "net_profit_margin": {"median": 0.08, "p25": 0.02, "p75": 0.15},
            "return_on_assets": {"median": 0.04, "p25": 0.01, "p75": 0.08},
            "return_on_equity": {"median": 0.10, "p25": 0.03, "p75": 0.18},
            "current_ratio": {"median": 1.4, "p25": 0.9, "p75": 2.0},
            "quick_ratio": {"median": 0.4, "p25": 0.2, "p75": 0.7},
            "debt_to_equity": {"median": 1.5, "p25": 0.7, "p75": 2.5},
            "debt_to_assets": {"median": 0.55, "p25": 0.40, "p75": 0.70},
            "asset_turnover": {"median": 0.5, "p25": 0.2, "p75": 0.8},
        }
    },
    "food_beverage": {
        "name_en": "Food & Beverage",
        "name_fa": "غذایی و نوشیدنی",
        "ratios": {
            "gross_profit_margin": {"median": 0.32, "p25": 0.22, "p75": 0.42},
            "net_profit_margin": {"median": 0.06, "p25": 0.02, "p75": 0.10},
            "return_on_assets": {"median": 0.07, "p25": 0.03, "p75": 0.12},
            "return_on_equity": {"median": 0.13, "p25": 0.06, "p75": 0.22},
            "current_ratio": {"median": 1.7, "p25": 1.1, "p75": 2.5},
            "quick_ratio": {"median": 0.8, "p25": 0.4, "p75": 1.3},
            "debt_to_equity": {"median": 0.7, "p25": 0.3, "p75": 1.2},
            "debt_to_assets": {"median": 0.38, "p25": 0.22, "p75": 0.55},
            "asset_turnover": {"median": 1.2, "p25": 0.7, "p75": 1.8},
            "inventory_turnover": {"median": 6.5, "p25": 4.0, "p75": 10.0},
            "receivables_turnover": {"median": 8.0, "p25": 5.0, "p75": 13.0},
        }
    },
}


def get_available_industries() -> list[dict]:
    """Return list of available industry benchmarks."""
    return [
        {"id": k, "name_en": v["name_en"], "name_fa": v["name_fa"]}
        for k, v in INDUSTRY_BENCHMARKS.items()
    ]


def compare_against_industry(
    company_ratios: list[dict],
    industry_id: str,
) -> dict:
    """Compare a company's ratios against an industry benchmark.
    
    Args:
        company_ratios: List of ratio dicts with 'ratio_name', 'value', 'unit'
        industry_id: Industry key from INDUSTRY_BENCHMARKS
    
    Returns:
        Benchmark comparison results with percentile rankings
    """
    if industry_id not in INDUSTRY_BENCHMARKS:
        raise ValueError(f"Unknown industry: {industry_id}. Available: {list(INDUSTRY_BENCHMARKS.keys())}")
    
    industry = INDUSTRY_BENCHMARKS[industry_id]
    industry_ratios = industry["ratios"]
    
    comparisons = []
    total_score = 0
    scored_count = 0
    
    for ratio in company_ratios:
        name = ratio["ratio_name"]
        value = ratio["value"]
        
        if name in industry_ratios:
            bench = industry_ratios[name]
            median = bench["median"]
            p25 = bench["p25"]
            p75 = bench["p75"]
            
            # Determine percentile rank
            if value >= p75:
                percentile = 90
                rank = "excellent"
            elif value >= median:
                percentile = 65
                rank = "above_average"
            elif value >= p25:
                percentile = 35
                rank = "below_average"
            else:
                percentile = 10
                rank = "poor"
            
            # For leverage ratios, invert the ranking (lower is better)
            if name in ("debt_to_equity", "debt_to_assets"):
                if value <= p25:
                    percentile = 90
                    rank = "excellent"
                elif value <= median:
                    percentile = 65
                    rank = "above_average"
                elif value <= p75:
                    percentile = 35
                    rank = "below_average"
                else:
                    percentile = 10
                    rank = "poor"
            
            # Calculate deviation from median
            deviation = ((value - median) / max(abs(median), 0.001)) * 100
            
            comparisons.append({
                "ratio_name": name,
                "company_value": value,
                "industry_median": median,
                "industry_p25": p25,
                "industry_p75": p75,
                "percentile": percentile,
                "rank": rank,
                "deviation_pct": round(deviation, 1),
            })
            
            total_score += percentile
            scored_count += 1
        else:
            comparisons.append({
                "ratio_name": name,
                "company_value": value,
                "industry_median": None,
                "industry_p25": None,
                "industry_p75": None,
                "percentile": None,
                "rank": "no_benchmark",
                "deviation_pct": None,
            })
    
    overall_percentile = round(total_score / scored_count) if scored_count > 0 else 0
    
    return {
        "industry_id": industry_id,
        "industry_name_en": industry["name_en"],
        "industry_name_fa": industry["name_fa"],
        "overall_percentile": overall_percentile,
        "overall_rank": _percentile_to_rank(overall_percentile),
        "comparisons": comparisons,
        "ratios_benchmarked": scored_count,
        "ratios_total": len(company_ratios),
        "recommendations": _generate_benchmark_recommendations(comparisons),
    }


def _percentile_to_rank(p: int) -> str:
    if p >= 75:
        return "excellent"
    elif p >= 50:
        return "above_average"
    elif p >= 25:
        return "below_average"
    return "poor"


def _generate_benchmark_recommendations(comparisons: list[dict]) -> list[str]:
    """Generate actionable recommendations based on benchmark gaps."""
    recs = []
    for c in comparisons:
        if c["rank"] == "poor":
            name = c["ratio_name"].replace("_", " ").title()
            median = c["industry_median"]
            value = c["company_value"]
            
            if c["ratio_name"] in ("debt_to_equity", "debt_to_assets"):
                recs.append(f"{name} is {value:.2f}x vs industry median {median:.2f}x — consider reducing leverage")
            elif "margin" in c["ratio_name"]:
                recs.append(f"{name} is significantly below industry average — review cost structure")
            elif "turnover" in c["ratio_name"]:
                recs.append(f"{name} is below industry norms — improve asset/receivables management")
            else:
                recs.append(f"{name} ({value:.2f}) lags behind industry median ({median:.2f}) — needs attention")
    
    return recs[:5]  # Top 5 most important


def auto_detect_industry(company_name: str, ratios: list[dict]) -> str:
    """Auto-detect industry based on company name patterns and ratio profiles."""
    name_lower = company_name.lower()
    
    # Name-based detection
    tech_keywords = ['tech', 'software', 'فناوری', 'نرم‌افزار', 'آی‌تی', 'اطلاعات', 'digital', 'compu']
    mfg_keywords = ['manufact', 'صنعت', 'تولید', 'فولاد', 'ذوب', 'سیمان', 'فولاد']
    retail_keywords = ['retail', 'فروشگاه', 'خرده', 'hyper', 'supermarket', 'مارکت']
    bank_keywords = ['bank', 'بانک', 'finance', 'مالی', 'سرمایه‌گذار', 'leasing', 'بورس']
    pharma_keywords = ['pharma', 'دارو', 'سینا', 'عبیدی', 'داروسازی', 'بهداشت']
    oil_keywords = ['oil', 'نفت', 'گاز', 'پتروشیمی', 'پالایش', 'refin', 'petro']
    re_keywords = ['real estate', 'املاک', 'ساختمان', 'عمران', 'مسکن', 'construct']
    food_keywords = ['food', 'غذا', 'لبنی', 'لبنیات', 'نوشیدنی', 'beverage', 'داریوش', 'کاله']
    
    keyword_map = {
        'technology': tech_keywords, 'manufacturing': mfg_keywords,
        'retail': retail_keywords, 'banking': bank_keywords,
        'pharmaceutical': pharma_keywords, 'oil_gas': oil_keywords,
        'real_estate': re_keywords, 'food_beverage': food_keywords,
    }
    
    for industry, keywords in keyword_map.items():
        if any(kw in name_lower for kw in keywords):
            return industry
    
    # Ratio profile-based detection (heuristic)
    ratio_dict = {r["ratio_name"]: r["value"] for r in ratios}
    
    gpm = ratio_dict.get("gross_profit_margin", 0)
    d_e = ratio_dict.get("debt_to_equity", 0)
    
    if gpm > 0.50 and d_e < 0.5:
        return "technology"
    if d_e > 5.0:
        return "banking"
    if gpm > 0.45:
        return "pharmaceutical"
    if gpm > 0.35 and d_e > 0.8:
        return "oil_gas"
    if gpm < 0.30 and d_e > 1.0:
        return "real_estate"
    
    return "manufacturing"  # Default
