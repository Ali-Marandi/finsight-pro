# FinSight Pro — Category-Creation Research Notes

## The core operational job remains unsolved

A 2025 finance-team survey reported by CFO.com found that half of respondents still take six or more business days to close, while reconciliation, fragmented data, manual corrections, and spreadsheet-led processes remain substantial blockers. The underlying job is not merely calculating ratios; it is turning heterogeneous, imperfect financial evidence into a number that a finance leader can defend.

A study of spreadsheet controls for financial reporting found lifecycle-control problems across the surveyed organizations. This supports treating spreadsheets as governed evidence that needs lineage, versioning, validation, review, and archiving—not as a disposable upload format.

## What the leading market already covers

The mature FP&A and close-management market already offers connected-source ingestion, budget-versus-actual variance detection, root-cause drill-down, narrative drafting, spreadsheet integrations, workflow, and audit trails. Cube, for example, explicitly promotes transaction-level variance tracing, driver attribution, explanations in existing work surfaces, access controls, and audit logging. Aleph’s market overview identifies similar capabilities across multiple modern FP&A products.

The implication is that FinSight Pro should not attempt to win as a small version of an FP&A platform or as another dashboard. Generic variance detection, PDF export, dashboards, and chat are increasingly table stakes. The space for a distinctive product lies before and around those workflows: resolving whether the financial evidence is comparable, complete, correctly mapped, and suitable for a specific decision.

## Trustworthy AI is a product feature, not a legal appendix

NIST’s AI RMF is intended to help organizations incorporate trustworthiness into AI product design, development, use, and evaluation. GAO describes AI benefits alongside data quality, privacy, bias, and cybersecurity risks, and notes that regulator AI outputs commonly inform staff decisions rather than serving as the sole decision source.

CFA Institute’s XAI research similarly argues that explainability, accountability, and human oversight are vital in finance. The most valuable user experience is therefore not an AI that announces a conclusion; it is an AI that constructs a decision case with source evidence, deterministic rules, uncertainty, alternative explanations, and an explicit human review state.

## Product opportunity inferred from the research

The candidate category is an **Evidence-to-Decision Operating System for Finance**. Its atomic unit is not a file, ratio, chart, or chatbot response. It is a **Decision Proof**: an inspectable object that records the source files, schema mappings, validation results, period/currency/scale assumptions, deterministic calculations, competing explanations, analyst judgment, reviewer approval, and rendered output.

The category wedge is a **Financial Evidence Compiler**. Users should be able to drop in imperfect local exports or documents and receive a compilation result: a normalized canonical statement, a data-quality and comparability score, a mapping trail, a list of unresolved ambiguities, and only then decision-ready analysis. This makes AI useful before the dashboard and makes each number portable, reviewable, and reusable.

## Sources

1. CFO.com, "50% of finance teams still take over a week to close the books" — https://www.cfo.com/news/50-of-finance-take-week-to-close-books-ledge-month-end-close-time-cfo-three-day-close-myth-/746085/
2. Grossman & Özlük, "Controls over Spreadsheets for Financial Reporting in Practice" — https://arxiv.org/abs/1111.6887
3. Cube, "Variance analysis" — https://www.cubesoftware.com/variance-analysis
4. Aleph, "AI-powered variance detection" — https://www.getaleph.com/answers/ai-fpa-software-variance-detection
5. NIST, "AI Risk Management Framework" — https://www.nist.gov/itl/ai-risk-management-framework
6. U.S. GAO, "Artificial Intelligence: Use and Oversight in Financial Services" — https://www.gao.gov/products/gao-25-107197
7. CFA Institute, "Explainable AI in Finance" — https://rpc.cfainstitute.org/research/reports/2025/explainable-ai-in-finance

## Global data substrate

XBRL International describes XBRL as a computer-readable global reporting standard that supports comparison across countries and languages, multilingual labels, data validation, and AI-ready structured inputs. The IFRS Foundation describes IFRS digital taxonomies as the tagged structure that makes IFRS-aligned information computer-readable. This supports an adapter-based roadmap: canonical financial concepts internally, explicit mapping/provenance at the edges, and XBRL/iXBRL as a later source adapter—not a shortcut to unlicensed commercial taxonomy use.

8. XBRL International, "What is XBRL?" — https://www.xbrl.org/the-standard/what/what-is-xbrl/
9. IFRS Foundation, "Digital financial reporting" — https://www.ifrs.org/digital-financial-reporting/
