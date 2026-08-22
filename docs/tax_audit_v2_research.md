# Research Notes — Tax-Audit AI, Firm Adoption, and Cloud Sync

## Professional-evidence implications

IAASB’s audit-evidence work explicitly considers issues arising from technology, professional skepticism, and the expanding sources of information available to auditors. Its ISA 500 Series work aims to modernize evidence standards in light of technology and reinforce consistent practice and professional skepticism. FinSight should therefore treat source provenance, reliability signals, reviewer challenge, and explicit uncertainty as core product behavior—not as report metadata added at the end. [1] [2]

## Trustworthy AI implications

NIST’s AI RMF is intended to help organizations incorporate trustworthiness into the design, development, use, and evaluation of AI products. Its Generative AI profile specifically addresses unique generative-AI risks. This supports a control architecture that records model/version/prompt context, retrieval sources, deterministic calculations, reviewer actions, evaluation outcomes, and incident response. [3]

## Accounting-firm demand and procurement implications

CPA.com and Blue J’s 2026 survey of more than 1,000 tax professionals reports that 60% use AI-powered tax research at least weekly, up from 33% in 2025. Respondents report use in advisory projects, tax planning, compliance research, document analysis, and drafting; 69% anticipate a value-based, hybrid, or fixed-fee billing shift. This supports selling FinSight as a controlled workflow for higher-value deliverables, not as a generic AI license. [4]

Thomson Reuters reports that 29% of firms identify data quality and consistency as a main barrier to automation. It also highlights sensitive PII, fragmented client formats, retention policies, security, data governance, encryption, and evidence of controls as important issues for firms considering AI and cloud tools. [5]

## Cloud-security implications

NIST’s Zero Trust Architecture states that implicit trust should not be granted based only on network location or asset ownership, and authentication/authorization should happen before access to an enterprise resource. For FinSight Cloud Sync, each organization, workspace, project, evidence object, and sync request must therefore be explicitly authorized; tenancy cannot be represented only by a database filter in application code. [6]

## Sources

[1] IAASB, "Audit Evidence" — https://www.iaasb.org/consultations-projects/audit-evidence
[2] IAASB, "ISA 500 Series" — https://www.iaasb.org/consultations-projects/isa-500-series
[3] NIST, "AI Risk Management Framework" — https://www.nist.gov/itl/ai-risk-management-framework
[4] CPA.com and Blue J, "AI Adoption Among Tax Firms Has Nearly Doubled" — https://www.cpa.com/news/blue-j-and-cpacom-survey-finds-ai-adoption-among-tax-firms-has-nearly-doubled-one-year
[5] Thomson Reuters, "Data management: Best practices for accounting firms" — https://tax.thomsonreuters.com/blog/data-management-best-practices-for-accounting-firms-tri/
[6] NIST, "Zero Trust Architecture" — https://www.nist.gov/publications/zero-trust-architecture
