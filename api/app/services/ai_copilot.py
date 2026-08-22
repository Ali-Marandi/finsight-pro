"""
AI Financial Copilot Service.
Provides intelligent chat interface for financial data analysis.

Supports multiple LLM backends:
- OpenAI-compatible APIs (OpenAI, DeepSeek, etc.)
- Local models via Ollama
- Built-in rule-based analysis (no API key required)
"""

import json
import httpx
from typing import Optional


# System prompt for the financial AI assistant
FINANCIAL_ANALYST_SYSTEM_PROMPT = """You are FinSight Pro AI, an expert financial analyst assistant. You analyze financial statements and provide clear, actionable insights.

Your capabilities:
- Analyze financial ratios and identify trends
- Explain what each ratio means in plain language
- Provide actionable recommendations based on financial data
- Compare performance against industry benchmarks
- Identify potential risks and opportunities
- Support both English and Persian (Farsi) responses

Guidelines:
- Be precise with numbers — always reference actual values from the data
- Structure responses with clear headings and bullet points
- Use traffic light indicators: green for good, amber for warning, red for critical
- Provide context — don't just state numbers, explain what they mean
- When asked in Persian, respond in Persian
- When asked in English, respond in English
- Always base your analysis on the provided data, not assumptions
- If the data is insufficient for a reliable conclusion, say so clearly

Response format:
- Use markdown formatting for structure
- Keep responses concise but thorough
- End with a brief summary of key takeaways
"""


def _build_context_message(analysis_data: dict) -> str:
    """Build a detailed context message from analysis data."""
    if not analysis_data:
        return ""
    
    company = analysis_data.get("company_name", "Unknown")
    period = analysis_data.get("period", "Unknown")
    ratios = analysis_data.get("ratios", [])
    
    # Group ratios by category
    categories = {}
    for r in ratios:
        cat = r.get("category", "other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r)
    
    context_lines = [
        f"## Financial Analysis Data for {company} ({period})",
        "",
    ]
    
    category_labels = {
        "profitability": "### Profitability Ratios",
        "liquidity": "### Liquidity Ratios",
        "leverage": "### Leverage / Solvency Ratios",
        "efficiency": "### Efficiency Ratios",
    }
    
    for cat, cat_ratios in categories.items():
        label = category_labels.get(cat, f"### {cat.title()} Ratios")
        context_lines.append(label)
        for r in cat_ratios:
            name = r.get("ratio_name", "Unknown").replace("_", " ").title()
            value = r.get("value", 0)
            unit = r.get("unit", "")
            benchmark = r.get("benchmark")
            status = r.get("status", "unknown")
            
            if unit == "%":
                value_str = f"{value * 100:.2f}%"
            elif unit == "x":
                value_str = f"{value:.2f}x"
            elif unit == "$":
                value_str = f"${value:,.0f}"
            elif unit == "days":
                value_str = f"{value:.1f} days"
            else:
                value_str = f"{value:.4f}"
            
            line = f"- **{name}**: {value_str}"
            if benchmark is not None:
                if unit == "%":
                    line += f" (Benchmark: {benchmark * 100:.1f}%)"
                elif unit == "x":
                    line += f" (Benchmark: {benchmark:.1f}x)"
                else:
                    line += f" (Benchmark: {benchmark})"
            line += f" [{status.upper()}]"
            context_lines.append(line)
        context_lines.append("")
    
    # Add category scores summary
    if ratios:
        score_map = {"good": 100, "warning": 60, "critical": 30}
        cat_scores = {}
        for r in ratios:
            cat = r.get("category")
            if cat not in cat_scores:
                cat_scores[cat] = []
            cat_scores[cat].append(score_map.get(r.get("status"), 50))
        
        context_lines.append("### Category Health Scores")
        for cat, scores in cat_scores.items():
            avg = sum(scores) / len(scores)
            bar = "#" * int(avg / 5) + "-" * (20 - int(avg / 5))
            context_lines.append(f"- {cat.title()}: [{bar}] {avg:.0f}/100")
    
    return "\n".join(context_lines)


def _build_prediction_context(prediction_data: dict) -> str:
    """Build context message from prediction results."""
    if not prediction_data:
        return ""
    
    lines = [
        "## Bankruptcy / Financial Distress Prediction Results",
        "",
        f"**Overall Assessment**: {prediction_data.get('overall_text', 'N/A')}",
        f"**Consensus Distress Probability**: {prediction_data.get('consensus_probability', 0)}%",
        "",
        "### Model Results:",
    ]
    
    for model in prediction_data.get("models", []):
        zone_emoji = {"safe": "🟢", "grey": "🟡", "distress": "🔴"}.get(model["zone"], "⚪")
        lines.append(
            f"- {model['model_name']} ({model['model_year']}): "
            f"Score={model['score']} | Zone={model['zone'].upper()} | "
            f"Distress Prob={model['probability']}% {zone_emoji}"
        )
    
    if prediction_data.get("recommendations"):
        lines.append("")
        lines.append("### Recommendations:")
        for i, rec in enumerate(prediction_data["recommendations"], 1):
            lines.append(f"{i}. {rec}")
    
    return "\n".join(lines)


async def chat_with_ai(
    message: str,
    analysis_data: Optional[dict] = None,
    prediction_data: Optional[dict] = None,
    conversation_history: Optional[list] = None,
    api_key: Optional[str] = None,
    api_endpoint: Optional[str] = None,
    model: str = "gpt-4o-mini",
) -> dict:
    """
    Send a message to the AI copilot and get a response.
    
    Args:
        message: User's question/message
        analysis_data: Financial analysis data (ratios, scores)
        prediction_data: Bankruptcy prediction results
        conversation_history: Previous messages in the conversation
        api_key: LLM API key (if None, uses built-in analysis)
        api_endpoint: LLM API endpoint URL
        model: Model name to use
    
    Returns:
        dict with 'response' text and 'sources' list
    """
    # If no API key, use built-in rule-based analysis
    if not api_key:
        return built_in_analysis(message, analysis_data, prediction_data)
    
    # Build messages for LLM
    messages = [{"role": "system", "content": FINANCIAL_ANALYST_SYSTEM_PROMPT}]
    
    # Add financial context
    context_parts = []
    if analysis_data:
        context_parts.append(_build_context_message(analysis_data))
    if prediction_data:
        context_parts.append(_build_prediction_context(prediction_data))
    
    if context_parts:
        context_msg = "\n\n---\n\n".join(context_parts)
        messages.append({
            "role": "system",
            "content": f"Here is the current financial data for analysis:\n\n{context_msg}",
        })
    
    # Add conversation history
    if conversation_history:
        for msg in conversation_history[-10:]:  # Last 10 messages for context
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })
    
    # Add current message
    messages.append({"role": "user", "content": message})
    
    # Determine endpoint
    endpoint = api_endpoint or "https://api.openai.com/v1"
    if not endpoint.endswith("/chat/completions"):
        if endpoint.endswith("/"):
            endpoint = endpoint.rstrip("/")
        if "/v1" not in endpoint:
            endpoint = f"{endpoint}/v1"
        endpoint = f"{endpoint}/chat/completions"
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 2000,
                },
            )
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data["choices"][0]["message"]["content"]
                return {
                    "response": ai_response,
                    "sources": ["AI Analysis (LLM)"],
                    "model_used": model,
                }
            else:
                error_detail = response.text[:500]
                return {
                    "response": f"Sorry, I encountered an error connecting to the AI service (HTTP {response.status_code}). Please check your API settings.\n\nError: {error_detail}",
                    "sources": [],
                    "error": f"HTTP {response.status_code}",
                }
    except httpx.TimeoutException:
        return {
            "response": "The AI service timed out. This might be due to network issues or a slow model response. Please try again or check your connection.",
            "sources": [],
            "error": "timeout",
        }
    except Exception as e:
        return {
            "response": f"Failed to connect to AI service: {str(e)}. Please verify your API endpoint and key in Settings.",
            "sources": [],
            "error": str(e),
        }


def built_in_analysis(
    message: str,
    analysis_data: Optional[dict] = None,
    prediction_data: Optional[dict] = None,
) -> dict:
    """
    Built-in rule-based financial analysis (no API key required).
    Provides intelligent responses based on the financial data patterns.
    """
    msg_lower = message.lower()
    
    # Detect language
    persian_chars = set("ابتثجحخدذرزژسشصضطظعغفقکگلمنوهی")
    is_persian = any(c in persian_chars for c in message)
    
    if not analysis_data and not prediction_data:
        if is_persian:
            return {
                "response": (
                    "سلام! من دستیار مالی FinSight Pro هستم. 🏦\n\n"
                    "برای شروع تحلیل، لطفاً یک صورت مالی آپلود کنید یا یک تحلیل موجود را انتخاب کنید. "
                    "سپس می‌توانید سوالات زیر را بپرسید:\n\n"
                    "- وضعیت کلی شرکت چطوره؟\n"
                    "- کدام نسبت‌ها مشکل دارند؟\n"
                    "- پیشنهاد بهبود چیست؟\n"
                    "- احتمال ورشکستگی چقدره؟"
                ),
                "sources": ["Built-in Analysis Engine"],
            }
        else:
            return {
                "response": (
                    "Hello! I'm your FinSight Pro AI Financial Assistant. 🏦\n\n"
                    "To get started, upload a financial statement or select an existing analysis. "
                    "Then you can ask me questions like:\n\n"
                    "- What's the overall financial health?\n"
                    "- Which ratios need attention?\n"
                    "- What are the improvement suggestions?\n"
                    "- What's the bankruptcy risk level?"
                ),
                "sources": ["Built-in Analysis Engine"],
            }
    
    response_parts = []
    
    if analysis_data:
        ratios = analysis_data.get("ratios", [])
        company = analysis_data.get("company_name", "the company")
        period = analysis_data.get("period", "")
        
        # Categorize
        categories = {"profitability": [], "liquidity": [], "leverage": [], "efficiency": []}
        for r in ratios:
            cat = r.get("category")
            if cat in categories:
                categories[cat].append(r)
        
        # Overall health question
        if any(kw in msg_lower for kw in ["overall", "summary", "health", "وضعیت", "خلاصه", "سلامت"]):
            if is_persian:
                response_parts.append(f"# گزارش سلامت مالی {company} ({period})\n")
            else:
                response_parts.append(f"# Financial Health Summary: {company} ({period})\n")
            
            for cat_name, cat_ratios in categories.items():
                if not cat_ratios:
                    continue
                good = sum(1 for r in cat_ratios if r["status"] == "good")
                warn = sum(1 for r in cat_ratios if r["status"] == "warning")
                crit = sum(1 for r in cat_ratios if r["status"] == "critical")
                total = len(cat_ratios)
                score = round((good * 100 + warn * 60 + crit * 30) / total)
                
                indicator = "🟢" if score >= 75 else ("🟡" if score >= 50 else "🔴")
                
                if is_persian:
                    cat_labels = {
                        "profitability": "سودآوری",
                        "liquidity": "نقدینگی",
                        "leverage": "اهرم مالی",
                        "efficiency": "بهره‌وری",
                    }
                else:
                    cat_labels = {
                        "profitability": "Profitability",
                        "liquidity": "Liquidity",
                        "leverage": "Leverage",
                        "efficiency": "Efficiency",
                    }
                
                label = cat_labels.get(cat_name, cat_name)
                response_parts.append(
                    f"{indicator} **{label}**: {score}/100 "
                    f"({good} good, {warn} warning, {crit} critical out of {total})"
                )
            
            # Overall score
            all_good = sum(1 for r in ratios if r["status"] == "good")
            all_total = len(ratios)
            overall = round(all_good / all_total * 100) if all_total > 0 else 0
            overall_indicator = "🟢" if overall >= 70 else ("🟡" if overall >= 40 else "🔴")
            
            if is_persian:
                response_parts.append(f"\n**امتیاز کلی**: {overall_indicator} {overall}%")
            else:
                response_parts.append(f"\n**Overall Score**: {overall_indicator} {overall}%")
        
        # Problems / issues question
        elif any(kw in msg_lower for kw in ["problem", "issue", "risk", "bad", "مشکل", "خطر", "بد", "نگران"]):
            critical_ratios = [r for r in ratios if r["status"] == "critical"]
            warning_ratios = [r for r in ratios if r["status"] == "warning"]
            
            if is_persian:
                response_parts.append(f"# نقاط نگرانی {company}\n")
            else:
                response_parts.append(f"# Areas of Concern: {company}\n")
            
            if critical_ratios:
                if is_persian:
                    response_parts.append("## 🔴 وضعیت بحرانی")
                else:
                    response_parts.append("## 🔴 Critical Issues")
                for r in critical_ratios:
                    name = r["ratio_name"].replace("_", " ").title()
                    val = r["value"]
                    unit = r["unit"]
                    val_str = f"{val*100:.2f}%" if unit == "%" else f"{val:.2f}"
                    response_parts.append(f"- **{name}**: {val_str} — requires immediate attention")
            
            if warning_ratios:
                if is_persian:
                    response_parts.append("\n## 🟡 وضعیت هشدار")
                else:
                    response_parts.append("\n## 🟡 Warning Areas")
                for r in warning_ratios:
                    name = r["ratio_name"].replace("_", " ").title()
                    val = r["value"]
                    unit = r["unit"]
                    val_str = f"{val*100:.2f}%" if unit == "%" else f"{val:.2f}"
                    response_parts.append(f"- **{name}**: {val_str} — monitor closely")
            
            if not critical_ratios and not warning_ratios:
                if is_persian:
                    response_parts.append("✅ هیچ نسبت بحرانی یا هشداری یافت نشد. وضعیت مالی خوب است!")
                else:
                    response_parts.append("✅ No critical or warning ratios found. Financial health looks good!")
        
        # Specific ratio question
        elif any(kw in msg_lower for kw in ["profit", "margin", "سود", "حاشیه"]):
            prof_ratios = categories.get("profitability", [])
            if prof_ratios:
                if is_persian:
                    response_parts.append("# تحلیل سودآوری\n")
                else:
                    response_parts.append("# Profitability Analysis\n")
                for r in prof_ratios:
                    name = r["ratio_name"].replace("_", " ").title()
                    val = r["value"]
                    status_icon = "🟢" if r["status"] == "good" else ("🟡" if r["status"] == "warning" else "🔴")
                    val_str = f"{val*100:.2f}%" if r["unit"] == "%" else f"{val:.2f}"
                    bm = r.get("benchmark")
                    bm_str = f" (Benchmark: {bm*100:.1f}%)" if bm and r["unit"] == "%" else f" (Benchmark: {bm})" if bm else ""
                    response_parts.append(f"{status_icon} **{name}**: {val_str}{bm_str}")
        
        elif any(kw in msg_lower for kw in ["liquidity", "cash", "current", "نقد", "وجه"]):
            liq_ratios = categories.get("liquidity", [])
            if liq_ratios:
                if is_persian:
                    response_parts.append("# تحلیل نقدینگی\n")
                else:
                    response_parts.append("# Liquidity Analysis\n")
                for r in liq_ratios:
                    name = r["ratio_name"].replace("_", " ").title()
                    val = r["value"]
                    status_icon = "🟢" if r["status"] == "good" else ("🟡" if r["status"] == "warning" else "🔴")
                    val_str = f"{val*100:.2f}%" if r["unit"] == "%" else f"{val:.2f}"
                    response_parts.append(f"{status_icon} **{name}**: {val_str}")
        
        elif any(kw in msg_lower for kw in ["leverage", "debt", "equity", "اهرم", "بدهی", "حقوق"]):
            lev_ratios = categories.get("leverage", [])
            if lev_ratios:
                if is_persian:
                    response_parts.append("# تحلیل اهرم مالی\n")
                else:
                    response_parts.append("# Leverage Analysis\n")
                for r in lev_ratios:
                    name = r["ratio_name"].replace("_", " ").title()
                    val = r["value"]
                    status_icon = "🟢" if r["status"] == "good" else ("🟡" if r["status"] == "warning" else "🔴")
                    val_str = f"{val*100:.2f}%" if r["unit"] == "%" else f"{val:.2f}"
                    response_parts.append(f"{status_icon} **{name}**: {val_str}")
        
        elif any(kw in msg_lower for kw in ["efficiency", "turnover", "بهره", "گردش"]):
            eff_ratios = categories.get("efficiency", [])
            if eff_ratios:
                if is_persian:
                    response_parts.append("# تحلیل بهره‌وری\n")
                else:
                    response_parts.append("# Efficiency Analysis\n")
                for r in eff_ratios:
                    name = r["ratio_name"].replace("_", " ").title()
                    val = r["value"]
                    status_icon = "🟢" if r["status"] == "good" else ("🟡" if r["status"] == "warning" else "🔴")
                    val_str = f"{val:.2f}x" if r["unit"] == "x" else f"{val:.1f} days" if r["unit"] == "days" else f"{val:.2f}"
                    response_parts.append(f"{status_icon} **{name}**: {val_str}")
        
        elif any(kw in msg_lower for kw in ["suggest", "improve", "recommend", "پیشنهاد", "بهبود", "توصیه"]):
            if is_persian:
                response_parts.append(f"# پیشنهادات بهبود {company}\n")
            else:
                response_parts.append(f"# Improvement Recommendations for {company}\n")
            
            # Analyze each category and give targeted advice
            for cat_name, cat_ratios in categories.items():
                bad_ratios = [r for r in cat_ratios if r["status"] in ("warning", "critical")]
                if not bad_ratios:
                    continue
                
                if is_persian:
                    cat_labels_fa = {
                        "profitability": "## سودآوری",
                        "liquidity": "## نقدینگی",
                        "leverage": "## اهرم مالی",
                        "efficiency": "## بهره‌وری",
                    }
                    tips = {
                        "profitability": [
                            "هزینه‌های عملیاتی را بازنگری و کاهش دهید",
                            "قیمت‌گذاری محصولات را بهینه‌سازی کنید",
                            "حاشیه سود ناخالص را از طریق مذاکره با تامین‌کنندگان بهبود دهید",
                        ],
                        "liquidity": [
                            "مدیریت موجودی کالا را بهبود دهید (JIT inventory)",
                            "شرایط پرداخت بدهی‌های کوتاه‌مدت را مذاکره کنید",
                            "وجه نقد بیشتری از طریق تسهیلات خط اعتباری تامین کنید",
                        ],
                        "leverage": [
                            "بدهی‌ها را بازسازی و به بلندمدت تبدیل کنید",
                            "سرمایه جدید از طریق سهامداران موجود جذب کنید",
                            "دارایی‌های غیرضروری را بفروشید و بدهی‌ها را کاهش دهید",
                        ],
                        "efficiency": [
                            "سیستم‌های وصول مطالبات را تقویت کنید",
                            "گردش موجودی را از طریق پیش‌بینی بهتر تقاضا بهبود دهید",
                            "دارایی‌های کم‌بازده را شناسایی و حذف کنید",
                        ],
                    }
                else:
                    cat_labels_fa = {
                        "profitability": "## Profitability",
                        "liquidity": "## Liquidity",
                        "leverage": "## Leverage",
                        "efficiency": "## Efficiency",
                    }
                    tips = {
                        "profitability": [
                            "Review and reduce operating expenses",
                            "Optimize pricing strategy based on market analysis",
                            "Improve gross margin through supplier negotiations",
                        ],
                        "liquidity": [
                            "Improve inventory management (consider JIT approach)",
                            "Negotiate better payment terms with short-term creditors",
                            "Secure a revolving credit facility for cash cushion",
                        ],
                        "leverage": [
                            "Restructure debt by converting short-term to long-term",
                            "Consider equity injection from existing shareholders",
                            "Sell underperforming assets to reduce debt burden",
                        ],
                        "efficiency": [
                            "Strengthen accounts receivable collection processes",
                            "Improve inventory turnover through better demand forecasting",
                            "Identify and divest low-return assets",
                        ],
                    }
                
                response_parts.append(cat_labels_fa.get(cat_name, f"## {cat_name}"))
                for i, r in enumerate(bad_ratios[:3], 1):
                    name = r["ratio_name"].replace("_", " ").title()
                    status_icon = "🔴" if r["status"] == "critical" else "🟡"
                    response_parts.append(f"{status_icon} {name}")
                
                cat_tips = tips.get(cat_name, [])
                for tip in cat_tips:
                    response_parts.append(f"  → {tip}")
                response_parts.append("")
        
        # Catch-all: provide a general analysis if specific keywords don't match
        elif not response_parts:
            if is_persian:
                response_parts.append(f"# تحلیل {company}\n")
                response_parts.append("در اینجا خلاصه‌ای از نسبت‌های مالی ارائه شده:")
            else:
                response_parts.append(f"# Analysis of {company}\n")
                response_parts.append("Here's a summary of the financial ratios:")
            
            for cat_name, cat_ratios in categories.items():
                if not cat_ratios:
                    continue
                if is_persian:
                    cat_labels = {"profitability": "سودآوری", "liquidity": "نقدینگی", "leverage": "اهرم", "efficiency": "بهره‌وری"}
                else:
                    cat_labels = {"profitability": "Profitability", "liquidity": "Liquidity", "leverage": "Leverage", "efficiency": "Efficiency"}
                response_parts.append(f"\n**{cat_labels.get(cat_name, cat_name)}:**")
                for r in cat_ratios:
                    name = r["ratio_name"].replace("_", " ").title()
                    val = r["value"]
                    status_icon = "🟢" if r["status"] == "good" else ("🟡" if r["status"] == "warning" else "🔴")
                    if r["unit"] == "%":
                        val_str = f"{val*100:.2f}%"
                    elif r["unit"] == "x":
                        val_str = f"{val:.2f}x"
                    else:
                        val_str = f"{val:.2f}"
                    response_parts.append(f"  {status_icon} {name}: {val_str}")
    
    # Prediction data analysis
    if prediction_data:
        if any(kw in msg_lower for kw in ["bankrupt", "distress", "predict", "ورشکست", "بحران", "پیش‌بینی"]):
            prob = prediction_data.get("consensus_probability", 0)
            overall = prediction_data.get("overall_assessment", "grey")
            models = prediction_data.get("models", [])
            recs = prediction_data.get("recommendations", [])
            
            zone_icons = {"safe": "🟢", "grey": "🟡", "distress": "🔴"}
            icon = zone_icons.get(overall, "⚪")
            
            if is_persian:
                response_parts.append("# پیش‌بینی ورشکستگی و بحران مالی\n")
                response_parts.append(f"**ارزیابی کلی**: {icon} {prediction_data.get('overall_text', '')}")
                response_parts.append(f"**احتمال اجماع بحران**: {prob}%\n")
            else:
                response_parts.append("# Bankruptcy & Financial Distress Prediction\n")
                response_parts.append(f"**Overall**: {icon} {prediction_data.get('overall_text', '')}")
                response_parts.append(f"**Consensus Distress Probability**: {prob}%\n")
            
            for m in models:
                m_icon = zone_icons.get(m["zone"], "⚪")
                response_parts.append(
                    f"{m_icon} **{m['model_name']}**: Score={m['score']} | "
                    f"Zone={m['zone'].upper()} | Probability={m['probability']}%"
                )
            
            if recs:
                response_parts.append("")
                if is_persian:
                    response_parts.append("## توصیه‌ها")
                else:
                    response_parts.append("## Recommendations")
                for rec in recs:
                    response_parts.append(f"- {rec}")
    
    # If nothing matched
    if not response_parts:
        if is_persian:
            response_parts.append(
                "متوجه شدم. لطفاً سوال خود را مشخص‌تر بپرسید. مثلاً:\n"
                "- وضعیت کلی مالی چطوره؟\n"
                "- کدام نسبت‌ها مشکل دارند؟\n"
                "- پیشنهاد بهبود چیست؟"
            )
        else:
            response_parts.append(
                "I understand. Could you be more specific? Try asking:\n"
                "- What's the overall financial health?\n"
                "- Which ratios need attention?\n"
                "- What improvements do you recommend?"
            )
    
    return {
        "response": "\n".join(response_parts),
        "sources": ["Built-in Analysis Engine"],
        "model_used": "rule-based",
    }
