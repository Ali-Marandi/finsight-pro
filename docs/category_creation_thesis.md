# FinSight Pro: از ابزار تحلیل نسبت به «سیستم اثبات تصمیم مالی»

## حکم اصلی

اگر FinSight Pro صرفاً یک ابزار ratio، dashboard، PDF یا چت‌بات مالی دیگر شود، بازار به دنبال آن نخواهد آمد. این قابلیت‌ها اکنون در FP&A، close-management و ابزارهای spreadsheet-native عرضه می‌شوند. پلتفرم‌هایی مانند Cube و Aleph از هم‌اکنون تحلیل واریانس، استخراج علت، روایت‌سازی، اتصال به spreadsheet و ردگیری تا سطح تراکنش را عرضه می‌کنند. [1] [2]

فرصت دسته‌ساز در نقطه‌ای **پیش از dashboard و پیرامون تصمیم** قرار دارد: بیشتر شرکت‌ها نمی‌دانند داده‌ای که وارد تحلیل شده آیا درست نگاشت شده، از نظر دوره/واحد/ارز قابل‌مقایسه است، کدام سلول یا فایل آن را پشتیبانی می‌کند، و کدام بخش هنوز مبهم است. این خلأ به‌خصوص در فایل‌های خروجی ناهمگون ERP، Excel، PDF، زبان‌های محلی و گروه‌های چندشرکتی دردناک است. گزارش‌های مالی همچنان با دادهٔ پراکنده، خطاهای دستی، Excel و reconciliation زمان‌بر درگیرند. [3] [4]

> **پیشنهاد دسته:** FinSight Pro باید به نخستین «Financial Evidence Compiler» تبدیل شود؛ سامانه‌ای که شواهد خام مالی را به یک **Decision Proof** قابل‌بررسی، قابل‌ردگیری و قابل‌استفادهٔ جهانی کامپایل می‌کند.

این ادعا به معنی اولین ابزار مالی جهان نیست. معنی دقیق‌تر و قابل‌دفاع آن این است که FinSight می‌تواند نخستین محصولی باشد که **ورودی‌های مالی نامرتب → مدل مفهومی استاندارد → کنترل کیفیت → تحلیل → توضیح AI → تأیید انسانی → بستهٔ اثبات تصمیم** را یک جریان واحد و قابل‌انتقال می‌سازد. این یک category design است، نه یک feature list.

## مسئله‌ای که باید مالک آن شویم

| پرسش مدیر مالی | وضعیت امروز | پاسخ FinSight Evidence |
|---|---|---|
| «آیا این عدد درست است؟» | فایل، نسخه و فرمول‌ها در چند پوشه/ایمیل پراکنده‌اند. | هر عدد به فایل، شیت، سلول، تبدیل، قاعده و تأییدکنندهٔ خود پیوند دارد. |
| «چرا این عدد تغییر کرد؟» | تحلیل‌گر با pivot و export دنبال علت می‌گردد. | سیستم ابتدا کیفیت و comparability را بررسی می‌کند، سپس علت را با سطح اطمینان و مسیر شواهد نشان می‌دهد. |
| «آیا دو شرکت/دوره قابل‌مقایسه‌اند؟» | تفاوت ارز، scale، fiscal calendar، chart of accounts و استاندارد پنهان است. | مقایسه فقط بعد از اعلان و تأیید زمینهٔ مالی امکان‌پذیر می‌شود. |
| «چه چیزی را هنوز نمی‌دانیم؟» | داشبورد معمولاً قطعیت کاذب می‌سازد. | Decision Proof یک بخش اجباری «ابهامات، دادهٔ ناقص و فرض‌ها» دارد. |
| «آیا می‌توانم این نتیجه را برای مدیر، حسابرس یا مشتری بفرستم؟» | نتیجه به تصویر، slide یا متن غیرقابل‌ردگیری تبدیل می‌شود. | بستهٔ امضاشدهٔ قابل‌خواندن برای انسان و قابل‌خواندن برای ماشین، با status بازبینی تولید می‌شود. |

این نقطهٔ تمرکز با واقعیت بازار هماهنگ است. گزارش CFO.com از ۲۰۲۵ نشان می‌دهد نیمی از تیم‌های مالی مورد بررسی بیش از شش روز کاری برای close زمان صرف می‌کنند و reconciliation، منابع دادهٔ پراکنده و فرایندهای Excelمحور از موانع اصلی‌اند. [3] پژوهش کنترل spreadsheet نیز نشان داده است که مشکل، تنها یک فرمول اشتباه نیست؛ کنترل‌های چرخهٔ عمر فایل در همهٔ مراحل دچار ضعف می‌شوند. [4]

## محصول پیشنهادی: FinSight Evidence

### ۱. «Evidence Compiler» به‌جای Upload

کاربر یک یا چند فایل CSV/XLSX، خروجی ERP یا در فاز بعد XBRL/iXBRL را وارد می‌کند. محصول به‌جای آن‌که فایل را فوراً به نمودار تبدیل کند، آن را **کامپایل** می‌کند:

1. ساختار فایل، شیت‌ها، عنوان‌ها، زبان، جهت متن، period، واحد، currency و scale را کشف می‌کند.
2. یک mapping پیشنهادی از ستون‌ها و ردیف‌ها به مفاهیم کانونی مالی می‌سازد.
3. کنترل‌های قطعی را اجرا می‌کند: تراز balance sheet، ناسازگاری sign، تکرار period، عدم تطابق واحد، مقادیر گمشده، پرش غیرعادی، و تضاد میان گزارش‌ها.
4. هر ابهام را با confidence و گزینهٔ تأیید انسانی نشان می‌دهد.
5. خروجی را به یک **Canonical Financial Graph** با metadata کامل تبدیل می‌کند.

نقطهٔ کلیدی این است که AI اجازه ندارد mapping یا توضیح را «حقیقت» اعلام کند. کاربر می‌بیند: «این ستون احتمالاً Accounts Receivable است، با ۷۶٪ اطمینان، زیرا نام آن X است و نسبت آن با Sales در بازهٔ Y قرار دارد؛ تأیید/اصلاح کنید.» این طراحی با نیاز AI قابل‌توضیح، کنترل انسانی و مدیریت خطر هماهنگ است. [5] [6] [7]

### ۲. «Truth Graph» به‌جای جدول نسبت

در مرکز محصول باید یک graph قرار بگیرد؛ نه فقط DataFrame. گره‌ها شامل source file، sheet، range، financial fact، account concept، period، currency، entity، transformation، validation rule، formula، insight، assumption و review هستند. هر نسبت یا AI insight از graph مشتق می‌شود.

نتیجه این است که هر کاربر می‌تواند از «Net margin ۱۲٪» به «فرمول»، سپس به «income statement row»، سپس به «سلول‌های فایل منبع» بازگردد. اگر داده یا mapping عوض شود، همهٔ proofهای وابسته فوراً stale می‌شوند و باید مجدداً بازبینی شوند. این همان ویژگی‌ای است که dashboardهای عادی ندارند: **اعداد به جای نمایش، زندگی‌نامه دارند.**

### ۳. «Decision Proof» به‌جای Report

Decision Proof محصول نهایی است. این یک شیء نسخه‌دار و قابل‌اشتراک است، نه PDF صرف.

| بخش | محتوا |
|---|---|
| سؤال تصمیم | مانند «آیا حاشیه سود عملیاتی این واحد در Q2 واقعاً افت کرده است؟» |
| دامنه و زمینه | entity، period، currency، scale، standard، comparator و materiality threshold |
| شواهد | فایل‌ها، نسخه‌ها، hash، mappingها، سلول‌ها و transformationها |
| کنترل‌ها | validationهای موفق، خطاها، exceptionهای پذیرفته‌شده و دلیل آن‌ها |
| تحلیل قطعی | نسبت‌ها، روندها و محاسبات تکرارپذیر |
| فرضیه‌های AI | علت‌های احتمالی با evidence، confidence و موارد unresolved |
| قضاوت انسانی | نظر تحلیل‌گر، اصلاح، امضا و approval state |
| خروجی | view تعاملی، HTML/PDF، و فایل machine-readable برای بازاستفاده |

این محصول باید به جای جواب دادن با قطعیت کاذب، سه وضعیت را به‌صورت واضح نمایش دهد: **تأییدشده، محتمل، نامشخص**. CFA Institute بر اهمیت explainability، accountability و human oversight در مالی تأکید می‌کند و GAO نیز نشان می‌دهد خروجی AI معمولاً باید به تصمیم انسانی اطلاع‌رسانی کند، نه اینکه جای آن را بگیرد. [6] [7]

### ۴. «AI Financial Investigator» نه Chatbot عمومی

AI در FinSight باید چهار وظیفهٔ محدود، قابل‌اندازه‌گیری و evidence-grounded داشته باشد:

| وظیفه | خروجی قابل‌قبول | خروجی ممنوع |
|---|---|---|
| Data detective | کشف ناهماهنگی، ambiguity و missing context | پرکردن خاموش دادهٔ مالی یا حدس‌زدن مبلغ واقعی |
| Mapping copilot | پیشنهاد mapping با شواهد و امکان override | اعمال mapping برگشت‌ناپذیر بدون تأیید |
| Root-cause investigator | hypothesisهای رتبه‌بندی‌شده با مسیر داده | جملهٔ علت‌محور بدون نشان‌دادن evidence |
| Narrative drafter | پیش‌نویس مدیریتی با citation داخلی و unresolved items | گزارش نهایی بدون امضای analyst |

این تفاوت مهم است؛ رقبا هم‌اکنون «why» و variance narrative را عرضه می‌کنند. مزیت FinSight باید **توضیحِ کیفیت شواهد قبل از توضیحِ تغییر عدد** باشد. یعنی ابتدا بپرسد: «آیا این variance واقعی است یا حاصل unit mismatch، mapping اشتباه یا incomplete data؟»

## نقطهٔ ورود بازار

### کاربر نخست: شرکت‌های حسابداری و advisory با مشتریان SMB چندفایلی

اولین بازار نباید enterprise CFO با ERPهای یکپارچه باشد؛ آن بازار از قبل با FP&A suites اشباع و خرید آن کند است. نقطهٔ ورود مناسب‌تر، **firmهای حسابداری، CFO-as-a-service و advisory** هستند که ماهانه دادهٔ ۲۰ تا ۲۵۰ مشتری با exportهای نامتجانس دریافت می‌کنند.

این گروه سه مزیت دارد: درد ورود داده را بارها تکرار می‌کند، به review و traceability نیاز دارد، و با هر mapping تأییدشده یک asset قابل‌استفاده برای مشتری بعدی تولید می‌کند. FinSight می‌تواند اول «Spreadsheet-to-Proof برای advisor» باشد، سپس به product داخلی finance team، بانک/وام‌دهنده، auditor و partnerهای ERP گسترش یابد.

### Wedge اولیه

**یک وعدهٔ کوچک اما خارق‌العاده:**

> «هر بستهٔ مالی ناهمگون را در چند دقیقه به یک تحلیل قابل‌دفاع تبدیل کن؛ یا دقیقاً ببین چرا هنوز قابل‌دفاع نیست.»

این وعده از «تحلیل خودکار» بهتر است، زیرا عدم قطعیت را نیز محصول می‌کند. اگر فایل بد است، مشتری به جای error مبهم یا dashboard گمراه‌کننده، یک diagnosis دقیق و کاربردی می‌گیرد.

## موتور دفاع‌پذیری

| لایه | چیزی که ساخته می‌شود | چرا تقلید آن سخت‌تر می‌شود |
|---|---|---|
| Financial ontology | مفاهیم کانونی، فرمول‌ها، unit/currency/period semantics و قاعده‌های استاندارد | فهم دامنه و coverage محلی/صنعتی به مرور انباشته می‌شود. |
| Mapping memory | templateهای قابل‌اشتراک و opt-in، synonymها و اصلاح‌های تأییدشده | با هر client file، دقت onboarding در حالت privacy-preserving بهتر می‌شود. |
| Evidence graph | lineage تا سطح cell/row، transformation و review status | ساختن traceability عمیق بعد از رشد محصول بسیار پرهزینه است. |
| Decision Proof format | قالب باز و versioned برای handoff به client، auditor و مدیر | اگر شریک‌ها proof را بخوانند، network effect ایجاد می‌شود. |
| Local-first trust | پردازش پیش‌فرض local/encrypted، اشتراک‌گذاری کنترل‌شده و data residency | برای بازارهای حساس به حریم خصوصی و حسابداری برون‌سپاری‌شده تمایز واقعی است. |

XBRL و taxonomyهای IFRS باید در roadmap دیده شوند، اما نه به‌عنوان MVP یا ادعای بی‌پایه. XBRL دادهٔ قابل‌خواندن برای ماشین، مقایسهٔ فرامرزی، برچسب چندزبانه و validation را ممکن می‌کند. [8] با این حال، IFRS اشاره می‌کند استفادهٔ تجاری از taxonomyها ممکن است نیازمند licence باشد؛ بنابراین adapterهای استاندارد باید بعد از بررسی حقوقی و تجاری ساخته شوند. [9]

## چه چیزی را نباید بسازیم

برای ساختن category، تمرکز حیاتی است. موارد زیر در مرحلهٔ اولیه نباید اولویت داشته باشند:

| ایدهٔ وسوسه‌انگیز | چرا نباید اکنون ساخته شود |
|---|---|
| Terminal دادهٔ بازار یا جایگزین Bloomberg | سرمایه‌بر، دارای مزیت شبکه‌ای شدید و خارج از wedge اصلی است. |
| ERP کامل | scope را منفجر و مسیر فروش را کند می‌کند. |
| Forecasting جعبه‌سیاه | بدون دادهٔ تمیز و provenance، اعتماد را از بین می‌برد. |
| Chatbot همه‌کاره | کپی‌پذیر و فاقد معیار success روشن است. |
| ۵۰ integration در شروع | ابتدا باید compiler و mapping loop روی فایل‌های واقعی عالی شود. |
| ادعای compliance یا توصیهٔ سرمایه‌گذاری | محصول باید تصمیم را پشتیبانی و مستند کند، نه تصمیم مالی شخصی یا حکم انطباق صادر کند. |

## تجربهٔ هدف در ۱۰ دقیقه

1. مشاور سه فایل مالی ماهانهٔ مشتری را می‌اندازد.
2. FinSight تشخیص می‌دهد واحدها در یکی «هزار ریال» و دیگری «ریال» هستند، دو عنوان متفاوت به یک مفهوم مالی نگاشت شده‌اند و balance sheet در یک period تراز نیست.
3. مشاور دو ambiguity را تأیید و یک مورد را برای مشتری برمی‌گرداند.
4. محصول یک Truth Graph و quality score شفاف می‌سازد.
5. AI سه hypothesis برای افت margin پیشنهاد می‌کند و به rows/transactions منبع لینک می‌دهد؛ موردی که evidence کافی ندارد «نامشخص» باقی می‌ماند.
6. مشاور Judgment خود را اضافه می‌کند و Decision Proof انگلیسی یا فارسی برای مشتری و مدیر مالی صادر می‌شود.
7. ماه بعد، mappingها و policyها دوباره استفاده می‌شوند و فقط exceptionها نیاز به توجه دارند.

این تجربه، «file upload → chart» نیست. **«messy evidence → defensible decision»** است.

## آزمایش‌های اعتبارسنجی پیش از توسعهٔ بزرگ

| آزمایش | آنچه باید بسنجیم | معیار تصمیم |
|---|---|---|
| Evidence clinic | ۱۵ تا ۲۰ فایل واقعیِ anonymized از advisorها در چند زبان/ERP | آیا product قبل از تحلیل، خطاها و ابهاماتی را کشف می‌کند که کاربران برایشان ارزش قائل‌اند؟ |
| Wizard of Oz mapping | پیشنهاد mapping با analyst انسانی پشت صحنه | آیا کاربر برای mapping trail و confidence حاضر است ابزار فعلی را ترک کند؟ |
| Proof review | یک Decision Proof برای CEO/client/auditor فرضی | آیا گیرنده بدون تماس اضافی می‌تواند نتیجه، شواهد و ابهام را بفهمد؟ |
| Repeatability | اجرای فایل ماه بعد با template قبلی | آیا زمان آماده‌سازی و تعداد اصلاح دستی واقعاً کم می‌شود؟ |
| Trust test | نمایش عمدی یک ambiguity یا false hypothesis | آیا کاربر شفافیت «نمی‌دانم» را بر پاسخ ظاهراً هوشمند ترجیح می‌دهد؟ |

اگر کاربران فقط dashboard یا PDF بخواهند، دستهٔ پیشنهادی کشش ندارد و باید کوچک بماند. اگر بابت proof، lineage و diagnosis پول یا دادهٔ واقعی برای آزمایش بدهند، signal اولیهٔ category fit ایجاد می‌شود.

## منابع

[1]: https://www.cubesoftware.com/variance-analysis "Cube — Variance analysis"
[2]: https://www.getaleph.com/answers/ai-fpa-software-variance-detection "Aleph — AI-powered variance detection"
[3]: https://www.cfo.com/news/50-of-finance-take-week-to-close-books-ledge-month-end-close-time-cfo-three-day-close-myth-/746085/ "CFO.com — 50% of finance teams still take over a week to close the books"
[4]: https://arxiv.org/abs/1111.6887 "Grossman & Özlük — Controls over Spreadsheets for Financial Reporting in Practice"
[5]: https://www.nist.gov/itl/ai-risk-management-framework "NIST — AI Risk Management Framework"
[6]: https://rpc.cfainstitute.org/research/reports/2025/explainable-ai-in-finance "CFA Institute — Explainable AI in Finance"
[7]: https://www.gao.gov/products/gao-25-107197 "U.S. GAO — Artificial Intelligence: Use and Oversight in Financial Services"
[8]: https://www.xbrl.org/the-standard/what/what-is-xbrl/ "XBRL International — What is XBRL?"
[9]: https://www.ifrs.org/digital-financial-reporting/ "IFRS Foundation — Digital financial reporting"
