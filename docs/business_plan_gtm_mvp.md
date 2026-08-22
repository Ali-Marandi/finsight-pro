# طرح کسب‌وکار، Go-to-Market و مشخصات MVP — FinSight Evidence

**نسخه:** ۰.۱ — مبتنی بر MVP پیاده‌سازی‌شده در مخزن  
**مخاطب:** مالک محصول، شریک اجرایی، شرکت‌های حسابداری و شریک‌های طراحی

## خلاصهٔ اجرایی

FinSight Evidence یک محصول local-first برای شرکت‌های حسابداری و advisory است که فایل‌های مالی ناهمگون مشتریان را پیش از تحلیل، **بازبینی‌پذیر و قابل‌اعتماد** می‌کند. وعدهٔ محصول «dashboard بیشتر» یا «AI همه‌کاره» نیست. وعده این است:

> **هر فایل مالی مشتری را به یک تحلیل قابل‌دفاع تبدیل کنید؛ یا دقیقاً ببینید چه چیزی مانع قابل‌دفاع بودن آن است.**

MVP اجراشده در این مخزن اولین بخش این وعده را عملی می‌کند: دریافت فایل CSV/XLSX، تشخیص schema، نگاشت قطعی و پیشنهادیِ انگلیسی/فارسی، بازبینی انسانی، ثبت source lineage تا سطح ردیف/ستون، و کنترل سلامت شواهد قبل از اجازهٔ تحلیل. این محصول مسئله‌ای را هدف می‌گیرد که فناوری‌های فعلی شرکت‌های حسابداری اغلب پیش از حل آن، به گزارش یا AI می‌پرند: **کیفیت، زمینه و قابلیت‌ردگیری دادهٔ مشتری.**

## ۱. مسئله و فرصت بازار

شرکت‌های حسابداری می‌خواهند از کارهای تکراری compliance به خدمات advisory باارزش‌تر حرکت کنند؛ اما دادهٔ مشتری همچنان در فایل‌های ناسازگار، spreadsheetها، خروجی‌های ERP و فرمت‌های محلی پراکنده است. در نظرسنجی Intuit در سال ۲۰۲۵، ۷۹٪ حسابداران رشد کار advisory را انتظار داشتند و هم‌زمان میانگین استفاده از هشت اپلیکیشن عملیاتی و دشواری integration/ورود دستی داده گزارش شد. [1] همچنین Thomson Reuters گزارش می‌کند ۲۹٪ firmها کیفیت و سازگاری داده را مانع اصلی اتوماسیون می‌دانند. [2]

| وضعیت موجود | اثر بر شرکت حسابداری | پاسخ FinSight Evidence |
|---|---|---|
| هر مشتری export و header متفاوت دارد. | زمان staff برای پاک‌سازی و mapping مصرف می‌شود. | mapping پیشنهادی و review-first، همراه با template قابل‌بازیافت در نسخه‌های بعدی. |
| فایل‌ها فاقد context ارز، واحد و period هستند. | تحلیل و مقایسه ممکن است اشتباه اما ظاهراً حرفه‌ای باشد. | Evidence Health قبل از dashboard و issueهای blocking/warning صریح. |
| AI متن تولید می‌کند اما منبع ندارد. | partner نمی‌تواند آن را به client نسبت دهد. | هر insight در roadmap باید به fact، mapping، rule و source location متصل باشد. |
| ابزارهای زیاد، adoption را سخت می‌کنند. | firm از محصول جدید اجتناب می‌کند. | local-first workflow محدود و سازگار با فایل‌های فعلی، نه جایگزینی ERP یا practice-management. |

CPA.com و Blue J در پژوهش ۲۰۲۶ خود گزارش کردند استفادهٔ هفتگی از AI در tax research به ۶۰٪ رسیده و advisory، تحلیل document و drafting جزو کاربردهای فعال‌اند؛ در عین حال، حرکت به مدل‌های value-based و hybrid billing در حال گسترش است. [3] این فرصت به FinSight اجازه می‌دهد به جای فروش «یک قابلیت AI»، ظرفیت تولید advisory deliverableهای قابل‌اعتماد را بفروشد.

## ۲. مشتری ایده‌آل و جایگاه‌یابی

### مشتری ایده‌آل اولیه (ICP)

| بُعد | تعریف پیشنهادی |
|---|---|
| نوع firm | accounting firm، CAS، CFO-as-a-service یا advisory firm با تحلیل دوره‌ای مشتریان SMB و mid-market. |
| اندازه | تیم ۵ تا ۵۰ نفر؛ به‌اندازه‌ای بزرگ که data cleanup تکراری باشد، اما بدون بودجه/چرخهٔ خرید enterprise. |
| workflow امروز | دریافت CSV/XLSX، خروجی QuickBooks/Xero/ERP یا workbookهای سفارشی؛ ساخت گزارش ماهانه یا advisory pack. |
| trigger خرید | افزایش clientهای advisory، فشار استخدام، error در گزارش، نیاز به استانداردسازی یا تمایل به استفادهٔ امن از AI. |
| buyer | managing partner، head of CAS/advisory یا مدیر عملیات. |
| champion | senior accountant، manager یا virtual CFO که هر ماه با فایل‌های واقعی درگیر است. |

### جایگاه‌یابی

**برای شرکت‌های حسابداری که دادهٔ مالی مشتریانشان نامنظم است، FinSight Evidence یک Financial Evidence Compiler است که exportهای ناهمگون را قبل از تحلیل به facts قابل‌ردگیری و reviewable تبدیل می‌کند؛ بر خلاف dashboardها و chatbotهای عمومی که روی دادهٔ تاییدنشده insight تولید می‌کنند.**

## ۳. مدل کسب‌وکار

### ارزش قابل‌فروش

واحد ارزش FinSight فایل نیست؛ **Decision Proof برای یک client-period** است. ارزش زمانی آشکار می‌شود که firm بتواند با زمان کمتر، staff کمتر و ریسک پایین‌تر، خروجی advisory قابل‌دفاع‌تری به مشتری تحویل دهد.

| جریان درآمد | طراحی پیشنهادی | منطق |
|---|---|---|
| Design Partner | هزینهٔ onboarding/enablement محدود به‌علاوهٔ دسترسی محصول در برابر بازخورد ساختارمند | از pilot رایگان بی‌پایان اجتناب می‌کند و willingness-to-pay را می‌سنجد. |
| Firm subscription | اشتراک بر پایهٔ analyst seat و محدودهٔ active client | با رشد خدمات advisory هم‌راستاست، نه با مصرف فایل خام. |
| Evidence add-on | templateهای پیشرفته، proof export، review workflow و retention controls | مشتری فقط زمانی ارتقا می‌دهد که اعتماد و استفادهٔ تکراری شکل گرفته باشد. |
| Partner enablement | onboarding، migration template، training و support حرفه‌ای | برای firmهای بزرگ‌تر، بدون تبدیل شرکت به خدمات سفارشی تمام‌وقت. |

قیمت‌گذاری عددی نباید پیش از ۵ تا ۱۰ design partner تثبیت شود. آزمایش willingness-to-pay باید سه عنصر را مقایسه کند: صرفه‌جویی در زمان آماده‌سازی، قابلیت استفادهٔ مجدد mapping، و توان تولید deliverable باارزش‌تر برای client. هر تخفیف باید در مقابل دادهٔ یادگیری، testimonial مشروط و جلسهٔ بازخورد تکرارشونده باشد.

### اقتصادی واحد

| فرضیه | سنجش لازم پیش از scale |
|---|---|
| acquisition | آیا یک evidence clinic با فایل anonymized به pilot تبدیل می‌شود؟ |
| activation | آیا champion در اولین جلسه یک issue واقعی یا mapping قابل‌استفاده پیدا می‌کند؟ |
| retention | آیا firm برای period دوم از template/review دوباره استفاده می‌کند؟ |
| expansion | آیا clientهای بیشتر یا analystهای بیشتر بعد از مشاهدهٔ proof اضافه می‌شوند؟ |
| gross margin | آیا onboarding از طریق template و workflow تکرارپذیر می‌شود یا به consulting دستی وابسته می‌ماند؟ |

## ۴. Go-to-Market برای جذب شرکت‌های حسابداری

### حرکت اول: Evidence Clinic

به‌جای demo عمومی dashboard، یک جلسهٔ کوتاه «Evidence Clinic» برگزار شود. firm یک فایل **anonymized** از بدترین یا زمان‌برترین بستهٔ ماهانه را می‌آورد. FinSight باید در همان جلسه یکی از این خروجی‌ها را ایجاد کند: mapping ambiguity، unit/period inconsistency، balance failure، یا template قابل‌بازیافت. اگر هیچ value واقعی پیدا نشود، محصول نباید به‌زور فروخته شود.

### قیف فروش پیشنهادی

| مرحله | پیشنهاد به prospect | معیار عبور |
|---|---|---|
| ۱. مسئله‌آگاهی | محتوای «Why your advisory report is only as good as its evidence» و checklist کیفیت فایل client | prospect یک درد واقعیِ intake/reporting را تایید کند. |
| ۲. Evidence Clinic | اجرای local-first روی یک فایل anonymized | دست‌کم یک issue، mapping یا time-saving معتبر کشف شود. |
| ۳. Design Partner Pilot | استفاده روی ۳ client تکراری و یک workflow ماهانه | champion بتواند بدون تیم FinSight proof/health review را تکرار کند. |
| ۴. Paid conversion | تبدیل workflow به subscription | firm برای active client/analyst بیشتر قرارداد بدهد. |
| ۵. Expansion | template catalog، team reviews، proof export و integration | mappingهای تاییدشده به clientهای بعدی یا periodهای بعدی تعمیم یابند. |

### کانال‌ها

| کانال | روش اجرا | دلیل تناسب |
|---|---|---|
| Founder-led outbound | تماس شخصی با partnerهای CAS/CFO-as-a-service بر پایهٔ signalهایی مثل service advisory یا استخدام accountant | در مرحلهٔ آغازین، feedback سریع‌تر از lead volume است. |
| Webinar/Workshop | «From messy client exports to reviewable advisory evidence» با نمونهٔ فایل anonymized | مسئله را به‌جای feature آموزش می‌دهد و trust می‌سازد. |
| اکوسیستم حرفه‌ای | جامعه‌های حسابداری، انجمن‌های CPA، شبکه‌های CFO و technology advisorها | buyerها به توصیهٔ همتای حرفه‌ای اعتماد بیشتری دارند. |
| ERP/Bookkeeping consultants | referral و template مشترک برای یک export رایج | consultant می‌تواند workflow مشتری را بدون جایگزینی stack بهبود دهد. |
| Content engine | Evidence Health Benchmark، قالب کنترل spreadsheet، و playbook نگاشت داده | ایجاد تقاضا حول category جدید، نه رقابت کلیدواژه‌ای با dashboard. |

### پیام‌های فروش

| نقش | پیام اصلی | اثبات در demo |
|---|---|---|
| Managing Partner | «کار advisory قابل‌دفاع‌تر، بدون استخدام بیشتر برای data cleanup.» | یک Decision Proof که client بتواند آن را بفهمد. |
| CAS/Advisory Lead | «فایل مشتری را قبل از اینکه گزارش خراب بسازد، استاندارد و review کنید.» | Evidence Health با blocker/remediation. |
| Senior Accountant | «دیگر لازم نیست headerها، scaleها و file mismatch را هر ماه از صفر پیدا کنید.» | mapping review و template reuse roadmap. |
| Client CFO | «هر عدد مهم مسیر شواهد دارد، نه یک answer مبهم AI.» | navigation از claim به source row/cell. |

### قواعد اعتماد و داده

GTM نباید ادعا کند FinSight جایگزین judgment حسابدار، compliance certification یا مشاورهٔ سرمایه‌گذاری است. محصول باید صریحاً بگوید AI پیشنهاد می‌دهد، validationهای قطعی را اجرا می‌کند و reviewer انسانی approval می‌دهد. Local-first processing، حداقل‌سازی دادهٔ ورودی، عدم استفادهٔ پیش‌فرض از فایل client برای آموزش، و سیاست retention روشن، بخشی از product marketing هستند؛ نه صفحهٔ حقوقی پنهان. این جهت با نگرانی‌های امنیت، PII و data governance شرکت‌های حسابداری هم‌راستاست. [2]

## ۵. مشخصات دقیق MVP اول

### هدف MVP

اثبات این فرضیه که یک شرکت حسابداری حاضر است پیش از تحلیل مالی، برای **Evidence Health و Mapping Review** وقت بگذارد، زیرا خطا و زمان rework را کاهش می‌دهد و خروجی قابل‌دفاع‌تری تولید می‌کند.

### قابلیت‌های اجراشده در مخزن

| قابلیت | رفتار دقیق | مسیر پیاده‌سازی |
|---|---|---|
| Intake محلی | CSV، XLSX و XLSM را بدون تغییر منبع می‌خواند و hash/metadata ایجاد می‌کند. | `src/finsight/evidence/intake.py` |
| Canonical schema | ۱۶ مفهوم پایه از period تا accounts receivable را می‌شناسد. | `CANONICAL_CONCEPTS` در `intake.py` |
| Alias detection | headerهای انگلیسی/فارسی مانند `Sales` یا `فروش` را به‌صورت **suggested** نگاشت می‌کند. | `ALIASES` و `propose_mappings()` |
| Human mapping review | پیشنهاد فقط بعد از override صریح کاربر به `confirmed` تبدیل می‌شود. | `apply_mapping_review()` |
| Evidence lineage | برای هر fact، file، sheet، column و row number نگهداری می‌شود. | `models.py` و `_canonical_facts()` |
| Evidence Health | missing concept، duplicate mapping، period تکراری، non-numeric value، تراز نبودن balance sheet و zero-revenue anomaly را بررسی می‌کند. | `validation.py` |
| Analysis gate | وجود issue مسدودکننده اجازهٔ ادامه به تحلیل را نمی‌دهد. | `EvidenceIntakeResult.is_ready_for_analysis` |
| API | endpoint `POST /evidence/inspect` فایل و overrideهای JSON را می‌پذیرد و payload بازبینی‌پذیر برمی‌گرداند. | `desktop/api/main.py` |
| UI | کاربر پس از upload ابتدا Mapping Review و Evidence Health می‌بیند؛ تحلیل فقط بعد از ready شدن فعال می‌شود. | `EvidenceReview.tsx` و `App.tsx` |
| i18n/RTL foundation | جریان انگلیسی و فارسی برای Evidence Review پشتیبانی می‌شود. | `desktop/frontend/src/i18n.ts` |

### معیار پذیرش MVP

1. فایل با canonical headerهای کامل، بدون issue blocking به تحلیل فعلی ratio راه پیدا کند.
2. alias مانند `Sales` به‌صورت suggestion نمایش یابد و بدون تأیید انسانی، تحلیل block شود.
3. تراز نبودن `assets ≠ liabilities + equity` به‌صورت issue مسدودکننده و همراه remediation نمایش یابد.
4. کاربر بتواند source column را به concept دیگری نگاشت یا از مدل فعلی خارج کند.
5. هر fact ایجادشده باید حداقل یک `EvidenceLocation` با file، sheet، column و row داشته باشد.
6. UI English LTR و Persian RTL در مسیر intake تا review build شود.
7. آزمون‌های هسته، endpoint و build frontend همگی موفق باشند.

### محدودهٔ آگاهانهٔ خارج از MVP

| مورد | دلیل عدم ورود به نسخهٔ اول |
|---|---|
| PDF Decision Proof و workflow امضا | ابتدا باید Evidence Health و mapping loop کشش واقعی نشان دهند. |
| ذخیرهٔ دائمی project و mapping template | نیازمند تصمیم صریح دربارهٔ encryption، retention و migration است. |
| اتصال مستقیم ERP | CSV/XLSX سریع‌ترین راه برای اعتبارسنجی workflow است. |
| XBRL/iXBRL import | به بررسی licence taxonomy و adapter تخصصی نیاز دارد. |
| AI root-cause آزاد | تا evidence graph و test set شکل نگیرد، خطر hallucination بالاست. |
| Multi-entity consolidation و FX conversion | context مالی و governance بیشتری می‌خواهد و scope را بزرگ می‌کند. |

## ۶. نمونه‌کدهای هستهٔ پردازش داده

### بررسی یک صورت مالی و دریافت health payload

```python
from finsight.evidence import inspect_statement

result = inspect_statement("client_statement.xlsx")

print(result.is_ready_for_analysis)
for issue in result.issues:
    print(issue.severity.value, issue.rule_id, issue.message)
```

### بازبینی انسانی یک alias پیشنهادی

```python
from finsight.evidence import inspect_statement

result = inspect_statement(
    "client_statement.csv",
    mapping_overrides={
        "Sales": "revenue",              # پیشنهاد به نگاشت تاییدشده تبدیل می‌شود
        "Internal note": None,             # از مدل مالی فعلی خارج می‌شود
    },
)

assert result.is_ready_for_analysis
```

### استفاده از Evidence Location برای lineage

```python
first_fact = result.facts[0]
source = first_fact.locations[0]
print(first_fact.concept_id, first_fact.value)
print(source.file_name, source.sheet_name, source.column_name, source.row_number)
```

### فراخوانی API از رابط یا ابزار داخلی

```bash
curl -X POST http://127.0.0.1:8400/evidence/inspect \
  -F "file=@client_statement.csv" \
  -F 'mapping_overrides={"Sales":"revenue"}'
```

پاسخ API شامل manifest، mappingها، health summary، ready-for-analysis و issueهای دارای remediation است. این قرارداد عمداً یک dataframe کامل یا فایل مشتری را برنمی‌گرداند؛ هدف آن ساخت یک لایهٔ reviewable است، نه افشای داده در رابط.

## ۷. نقشهٔ مسیر بعد از MVP

| گام | محصول | شرط آغاز |
|---|---|---|
| ۱. Template memory | ذخیرهٔ محلی mappingهای تاییدشده برای همان firm/client type | حداقل چند period تکراری در pilot و شواهد reuse. |
| ۲. Decision Proof | سؤال تصمیم، evidence graph، validation summary و HTML export نسخه‌دار | کاربران برای shareable deliverable درخواست واقعی بدهند. |
| ۳. AI Investigator محدود | hypothesis با evidence refs، confidence و unknown state | test set واقعی و reviewer feedback loop آماده باشد. |
| ۴. Secure project store | encryption، retention، role/review history | firmها بخواهند پرونده‌ها را بین analystها به اشتراک بگذارند. |
| ۵. Source adapters | یک ERP/export پرتکرار، سپس XBRL/iXBRL در صورت licence مناسب | CSV/XLSX wedge موفق و template model تثبیت شده باشد. |

## ۸. داشبورد تصمیم‌گیری برای مالک محصول

| پرسش راهبردی | داده‌ای که باید جمع شود | تصمیم ممکن |
|---|---|---|
| آیا Evidence Health ارزش ایجاد می‌کند؟ | تعداد issue واقعی، میزان اصلاح دستی و واکنش champion در clinic | ادامه/تغییر wedge |
| آیا firm پول می‌دهد؟ | conversion clinic→pilot و pilot→paid | تثبیت packaging و قیمت |
| آیا mapping قابل‌تعمیم است؟ | reuse template در دوره/مشتری بعدی | سرمایه‌گذاری در mapping memory |
| آیا AI اعتماد می‌سازد؟ | درصد reviewer acceptance، correction و abstention | افزودن/تعویق AI investigator |
| آیا product وارد workflow می‌شود؟ | استفادهٔ تکراری در close/advisory cycle | توسعهٔ team workflow یا توقف scale |

## منابع

[1]: https://investors.intuit.com/news-events/press-releases/detail/1263/accountants-embrace-ai-and-strategic-advisory-services-to-fuel-growth-yet-continue-to-face-tech-and-talent-barriers-according-to-2025-intuit-quickbooks-survey "Intuit — 2025 Accountant Technology Survey"
[2]: https://tax.thomsonreuters.com/blog/data-management-best-practices-for-accounting-firms-tri/ "Thomson Reuters — Data management best practices for accounting firms"
[3]: https://www.cpa.com/news/blue-j-and-cpacom-survey-finds-ai-adoption-among-tax-firms-has-nearly-doubled-one-year "CPA.com and Blue J — AI adoption among tax firms"
