r"""Sentiment Analysis Engine — NLP-based news/social media sentiment for Iranian market.

Provides rule-based sentiment scoring with keyword matching, negation handling,
and entity-level sentiment aggregation. Works offline — no external API calls.

Supports Persian (Farsi) and English text analysis.
"""

import re
import math
from typing import Optional
from collections import Counter


# ── Persian Sentiment Lexicons ──────────────────────────────────────────────

POSITIVE_FA = [
    # Growth / Profit
    'رشد', 'افزایش', 'بالا', 'صعود', 'مثبت', 'سود', 'منفعت', 'موفق', 'موفقیت',
    'بهبود', 'پیشرفت', 'کسب', ' Gewinn', 'تعالی', 'عالی', 'خوب', 'مطلوب',
    'بازگشت', 'بهار', 'رونق', 'توسعه', 'گسترش', 'رقم', 'عدد', 'ثروت',
    'پایدار', 'باثبات', 'قوی', 'قدرتمند', 'امیدوار', 'خوشبین', 'مثبت',
    # Market / Price
    'بالاتر', 'اکسپایری', 'پرطرفدار', 'محبوب', 'رکورد', 'تاریخی',
    'صعودی', 'bullish', 'مثبت', 'نور', 'سبز', 'خرس', 'گاو',
    # Company
    'سودآور', 'کارآمد', 'کارا', 'مثمر', 'پرسود', 'سودده', 'صادرات',
    'تولید', 'فروش', 'درآمد', 'جذب', 'نقدینگی', 'تقسیم', 'Dividend',
    # Quality
    'کیفیت', 'نوآوری', 'ایده', 'اختراع', 'برند', 'اعتبار', 'اعتماد',
    'شفاف', 'شفافیت', 'مدیریت', 'حرفه‌ای', 'مجرب', 'کارشناس',
]

NEGATIVE_FA = [
    # Decline / Loss
    'افت', 'کاهش', 'پایین', 'نزول', 'منفی', 'ضرر', 'زیان', 'بحران',
    ' شکست', 'ناامید', 'بد', 'ضعیف', 'نامطلوب', 'فاجعه', 'خرابی',
    ' regression', 'بازگشت', 'زمستان', 'رکود', 'کاهش', 'انقباض', 'فشار',
    'نامطمئن', 'بی‌ثبات', 'ناپایدار', 'ضعف', 'ناامید', 'بدبین', 'منفی',
    # Market / Price
    'پایین‌تر', 'بی‌طرف', 'نامطلوب', 'نوسان', 'تلاطم', 'ریسک',
    'نزولی', 'bearish', 'قرمز', 'سیاه', 'سقوط', 'افت شدید',
    # Company
    'زیان‌ده', 'بدهی', 'ممنوع', 'تحریم', 'محدود', 'کاهش سرمایه',
    'تعدیل', 'آسیب', 'ورشکستگی', 'توقیف', 'جریمه', 'عقب‌نشینی',
    # Quality
    'تقلب', 'فساد', 'شبهه', 'اختلاف', 'تنش', 'دعوا', 'مجازات',
    'حبس', 'بازداشت', 'تحقیق', 'ذخیره', 'ابهام', 'عدم شفافیت',
]

INTENSIFIERS_FA = ['بسیار', 'خیلی', 'شدیدا', 'کاملا', 'مطلقا', 'نسبتا', 'به‌شدت', 'به‌طرز', 'فوق‌العاده', 'نهایتا', 'به‌غایت']
NEGATORS_FA = ['نه', 'نمی', 'نخواهد', 'نبود', 'نیست', 'نباید', 'بدون', 'عدم', 'مخالف', 'برخلاف', 'غیر']

# ── English Sentiment Lexicons ─────────────────────────────────────────────

POSITIVE_EN = [
    'growth', 'increase', 'rise', 'gain', 'profit', 'surge', 'bullish',
    'outperform', 'beat', 'exceed', 'upgrade', 'strong', 'robust', 'solid',
    'improve', 'positive', 'opportunity', 'dividend', 'expansion', 'innovation',
    'record', 'high', 'boom', 'rally', 'breakthrough', 'efficient', 'optimal',
    'stable', 'recovery', 'momentum', 'confidence', 'trust', 'transparent',
    'buy', 'long', 'overweight', 'upgrade', 'initiate', 'acquire', 'merger',
]

NEGATIVE_EN = [
    'decline', 'decrease', 'fall', 'drop', 'loss', 'crash', 'bearish',
    'underperform', 'miss', 'downgrade', 'weak', 'poor', 'negative', 'risk',
    'worse', 'deteriorate', 'crisis', 'recession', 'debt', 'default', 'bankrupt',
    'low', 'bust', 'correction', 'squeeze', 'volatile', 'uncertainty', 'fraud',
    'sell', 'short', 'underweight', 'downgrade', 'cut', 'layoff', 'fine',
    'sanction', 'penalty', 'investigation', 'lawsuit', 'conflict', 'tension',
]

INTENSIFIERS_EN = ['very', 'extremely', 'highly', 'absolutely', 'significantly',
                     'remarkably', 'exceptionally', 'particularly', 'especially', 'incredibly']
NEGATORS_EN = ['not', 'no', 'never', 'neither', 'nor', 'hardly', 'barely', 'scarcely',
               'without', 'lack', 'absence', 'despite', 'excluding']


def _detect_lang(text: str) -> str:
    """Detect if text is primarily Persian or English."""
    fa_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    en_chars = len(re.findall(r'[a-zA-Z]', text))
    return 'fa' if fa_chars > en_chars else 'en'


def _tokenize_fa(text: str) -> list[str]:
    """Simple Persian tokenizer."""
    # Normalize
    text = text.replace('\u200c', ' ').replace('\u200d', ' ')  # ZWNJ, ZWJ
    text = re.sub(r'[\u064B-\u065F\u0670]', '', text)  # Remove diacritics
    # Tokenize
    tokens = re.findall(r'[\u0600-\u06FF]+|[a-zA-Z]+|[0-9.]+', text)
    return [t.lower() for t in tokens]


def _tokenize_en(text: str) -> list[str]:
    """Simple English tokenizer."""
    return re.findall(r'[a-zA-Z]+', text.lower())


def _score_text(text: str, lang: str) -> dict:
    """Score a single text's sentiment."""
    if lang == 'fa':
        tokens = _tokenize_fa(text)
        pos_lex = POSITIVE_FA
        neg_lex = NEGATIVE_FA
        intensifiers = set(INTENSIFIERS_FA)
        negators = set(NEGATORS_FA)
    else:
        tokens = _tokenize_en(text)
        pos_lex = POSITIVE_EN
        neg_lex = NEGATIVE_EN
        intensifiers = set(INTENSIFIERS_EN)
        negators = set(NEGATORS_EN)

    pos_score = 0.0
    neg_score = 0.0
    pos_words = []
    neg_words = []

    for i, token in enumerate(tokens):
        multiplier = 1.0
        negated = False

        # Check previous 2 words for intensifiers/negators
        for j in range(max(0, i - 2), i):
            if tokens[j] in intensifiers:
                multiplier *= 1.5
            if tokens[j] in negators:
                negated = True

        if token in pos_lex:
            if negated:
                neg_score += 0.8 * multiplier
                neg_words.append(token)
            else:
                pos_score += 1.0 * multiplier
                pos_words.append(token)
        elif token in neg_lex:
            if negated:
                pos_score += 0.5 * multiplier
                pos_words.append(token)
            else:
                neg_score += 1.0 * multiplier
                neg_words.append(token)

    total = pos_score + neg_score
    if total == 0:
        sentiment_score = 0.0
        sentiment_label = 'neutral'
    else:
        sentiment_score = (pos_score - neg_score) / total  # [-1, 1]
        if sentiment_score > 0.2:
            sentiment_label = 'positive'
        elif sentiment_score < -0.2:
            sentiment_label = 'negative'
        else:
            sentiment_label = 'neutral'

    return {
        'pos_score': round(pos_score, 3),
        'neg_score': round(neg_score, 3),
        'sentiment_score': round(sentiment_score, 4),
        'label': sentiment_label,
        'pos_words': pos_words[:5],
        'neg_words': neg_words[:5],
        'token_count': len(tokens),
    }


def analyze_sentiment(
    texts: list[str],
    labels: list[str] | None = None,
    weights: list[float] | None = None,
) -> dict:
    """Analyze sentiment for a batch of texts.

    Args:
        texts: List of text strings (news headlines, social posts, etc.).
        labels: Optional labels for each text (e.g., source names).
        weights: Optional importance weights per text.
    """
    if not texts:
        return {'error': 'No texts provided'}

    n = len(texts)
    if labels is None:
        labels = [f'Text {i+1}' for i in range(n)]
    if weights is None:
        weights = [1.0] * n

    results = []
    score_sum = 0.0
    weight_sum = 0.0
    label_counts = Counter()

    for i, text in enumerate(texts):
        lang = _detect_lang(text)
        score = _score_text(text, lang)
        score['text_preview'] = text[:120] + ('...' if len(text) > 120 else '')
        score['label_name'] = labels[i]
        score['lang'] = lang
        score['weight'] = weights[i]
        results.append(score)

        score_sum += score['sentiment_score'] * weights[i]
        weight_sum += weights[i]
        label_counts[score['label']] += 1

    avg_score = score_sum / weight_sum if weight_sum > 0 else 0
    if avg_score > 0.2:
        overall_label = 'positive'
    elif avg_score < -0.2:
        overall_label = 'negative'
    else:
        overall_label = 'neutral'

    # Sentiment distribution
    pos_count = sum(1 for r in results if r['label'] == 'positive')
    neg_count = sum(1 for r in results if r['label'] == 'negative')
    neu_count = sum(1 for r in results if r['label'] == 'neutral')

    # Top keywords
    all_pos = []
    all_neg = []
    for r in results:
        all_pos.extend(r['pos_words'])
        all_neg.extend(r['neg_words'])
    top_positive = [w for w, _ in Counter(all_pos).most_common(10)]
    top_negative = [w for w, _ in Counter(all_neg).most_common(10)]

    # Time series (if labels are dates or ordered)
    score_series = [round(r['sentiment_score'], 4) for r in results]

    return {
        'overall': {
            'score': round(avg_score, 4),
            'label': overall_label,
            'positive_pct': round(pos_count / n * 100, 1),
            'negative_pct': round(neg_count / n * 100, 1),
            'neutral_pct': round(neu_count / n * 100, 1),
        },
        'distribution': {
            'positive': pos_count,
            'negative': neg_count,
            'neutral': neu_count,
        },
        'top_keywords': {
            'positive': top_positive,
            'negative': top_negative,
        },
        'score_series': score_series,
        'texts': results,
        'total_texts': n,
    }


def stock_sentiment_analysis(
    symbol: str,
    news_texts: list[str],
    social_texts: list[str] | None = None,
) -> dict:
    """Analyze sentiment specifically for a stock symbol.

    Combines news and social media sentiment with weighted aggregation.
    """
    if not news_texts:
        return {'error': 'No news texts provided'}

    # Analyze news (weight 2x)
    news_labels = [f'{symbol} - News {i+1}' for i in range(len(news_texts))]
    news_weights = [2.0] * len(news_texts)
    news_result = analyze_sentiment(news_texts, news_labels, news_weights)

    # Analyze social (weight 1x)
    social_result = None
    if social_texts and len(social_texts) > 0:
        social_labels = [f'{symbol} - Social {i+1}' for i in range(len(social_texts))]
        social_weights = [1.0] * len(social_texts)
        social_result = analyze_sentiment(social_texts, social_labels, social_weights)

    # Combined score
    if social_result:
        total_news_weight = sum(news_weights)
        total_social_weight = len(social_texts)
        combined_score = (
            news_result['overall']['score'] * total_news_weight +
            social_result['overall']['score'] * total_social_weight
        ) / (total_news_weight + total_social_weight)
    else:
        combined_score = news_result['overall']['score']

    if combined_score > 0.2:
        signal = 'bullish'
    elif combined_score < -0.2:
        signal = 'bearish'
    else:
        signal = 'neutral'

    return {
        'symbol': symbol,
        'combined_score': round(combined_score, 4),
        'signal': signal,
        'news_sentiment': {
            'score': news_result['overall']['score'],
            'label': news_result['overall']['label'],
            'article_count': len(news_texts),
        },
        'social_sentiment': {
            'score': social_result['overall']['score'] if social_result else None,
            'label': social_result['overall']['label'] if social_result else None,
            'post_count': len(social_texts) if social_texts else 0,
        },
        'keyword_summary': {
            'positive': news_result['top_keywords']['positive'][:5],
            'negative': news_result['top_keywords']['negative'][:5],
        },
        'recommendation': _generate_recommendation(combined_score, signal),
    }


def _generate_recommendation(score: float, signal: str) -> str:
    """Generate a brief recommendation based on sentiment."""
    if signal == 'bullish':
        if score > 0.5:
            return 'Strong positive sentiment detected. Consider increasing position or initiating coverage. Monitor for sentiment reversal.'
        else:
            return 'Moderately positive sentiment. Current sentiment supports holding or cautiously adding to position.'
    elif signal == 'bearish':
        if score < -0.5:
            return 'Strong negative sentiment detected. Consider reducing exposure or setting tighter stop-losses. Wait for sentiment stabilization.'
        else:
            return 'Moderately negative sentiment. Exercise caution. May present buying opportunity if fundamentals remain strong.'
    else:
        return 'Neutral sentiment. No strong directional signal from sentiment analysis. Rely on fundamental and technical analysis for decisions.'


def sentiment_demo() -> dict:
    """Generate demo sentiment analysis with sample TSE news."""
    news = [
        'سود خالص شرکت فولاد مبارکه ۴۰ درصد افزایش یافت و به رکورد تاریخی رسید',
        'صادرات پتروشیمی خلیج فارس رشد ۲۵ درصدی نسبت به سال قبل دارد',
        'بانک مرکزی نرخ بهره را بدون تغییر نگه داشت — بازار واکنش مثبت نشان داد',
        'افت قیمت نفت جهانی فشار فروش بر سهام پالایشی وارد کرد',
        'گزارش ماهانه: شاخص کل بورس تهران با رشد ۳ درصدی بسته شد',
        'سهام خودروسازی ایران با افزایش تقاضا مواجه شد — خبر مثبت برای سهامداران',
        'تحریم‌های جدید ممکن است بر صادرات شرکت‌های دارویی تأثیر منفی بگذارد',
        'مدیرعامل فناوری اطلاعات: درآمد ما ۵۰ درصد رشد کرده و سودآوری بهبود یافته',
        'کاهش سرمایه بانک صادرات نگرانی سهامداران را افزایش داد',
        'توسعه زیرساخت‌های digital banking توسط بانک ملت — نوآوری در صنعت بانکداری',
        'نوسانات شدید بازار ارز بر سودآوری شرکت‌های进口‌کننده تأثیر منفی گذاشت',
        'تحلیلگران: چشم‌انداز مثبت برای سهام технологی در سال آینده',
    ]

    social = [
        'فولاد عالی بود امروز! 🚀 خریداری کردم',
        'پتروشیمی افت کرد، نگرانم 😟',
        'بانک صادرات رو نخرید! ضرر کردم',
        'شاخص مثبته، بازار داره برمی‌گرده 💪',
        'خودرو خوب پیش میره، سود خوبی داره',
        'تحریم‌ها داره ضرر میزنه به همه چیز 😔',
    ]

    # Per-stock analysis
    stock_news = {
        'فولاد': [
            'سود خالص شرکت فولاد مبارکه ۴۰ درصد افزایش یافت',
            'صادرات فولاد رشد ۳۰ درصدی داشت',
            'قیمت جهانی فولاد افت ۵ درصدی را تجربه کرد',
        ],
        'پتروشیمی': [
            'صادرات پتروشیمی خلیج فارس رشد ۲۵ درصدی',
            'افت قیمت نفت فشار بر پتروشیمی‌ها',
        ],
        'بانک': [
            'نرخ بهره بدون تغییر ماند',
            'کاهش سرمایه بانک صادرات',
            'نوآوری digital banking در بانک ملت',
        ],
        'خودرو': [
            'افزایش تقاضا برای سهام خودروسازی',
            'خبر مثبت برای سهامداران خودرو',
        ],
        'فناوری': [
            'درآمد فناوری اطلاعات ۵۰ درصد رشد کرد',
            'چشم‌انداز مثبت برای سهام تکنولوژی',
        ],
    }

    stock_results = []
    for sym, texts in stock_news.items():
        r = stock_sentiment_analysis(sym, texts)
        stock_results.append({
            'symbol': sym,
            'score': r['combined_score'],
            'signal': r['signal'],
            'news_count': r['news_sentiment']['article_count'],
            'recommendation': r['recommendation'],
        })

    # Overall market sentiment
    overall = analyze_sentiment(news, ['News ' + str(i+1) for i in range(len(news))])

    return {
        'demo_info': {
            'description': 'Demo sentiment analysis with 12 TSE news articles + 6 social posts',
            'news_count': len(news),
            'social_count': len(social),
            'stocks_analyzed': list(stock_news.keys()),
        },
        'market_overall': overall['overall'],
        'market_distribution': overall['distribution'],
        'market_keywords': overall['top_keywords'],
        'score_timeline': overall['score_series'],
        'per_stock': stock_results,
    }
