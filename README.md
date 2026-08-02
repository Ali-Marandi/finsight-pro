# FinSight Pro 📊



**FinSight Pro** is a professional-grade financial statement analytics engine. It transforms raw financial data from CSV or Excel files into comprehensive analytical reports with validated ratios, interactive-ready dashboards, and portable HTML reports.



## Features



- **Automated Ratio Calculation**: Includes Profitability, Liquidity, Leverage, and Efficiency ratios.
- 
- **Visual Dashboards**: Automatically generates a high-resolution performance dashboard using Matplotlib.
- 
- **Portable HTML Reports**: Modern, responsive reports that are easy to share and view in any browser.
- 
- **Multi-format Ingestion**: Supports CSV and Excel (`.xlsx`, `.xlsm`) files.
- 
- **Strict Data Validation**: Ensures data integrity with schema validation and numeric consistency checks.
- 


## Installation



```bash

pip install .

```



*Note: Requires Python 3.10+ and dependencies like `pandas`, `matplotlib`, and `openpyxl`.*



## Usage



### Command Line Interface



Analyze a financial statement and generate reports in a specific directory:



```bash

finsight path/to/statement.csv --output ./reports

```



### Required Data Schema



The input file must contain the following columns:



| Category | Columns |

| --- | --- |

| **Identity** | `period` (e.g., 2023, Q1-2024) |

| **Income Statement** | `revenue`, `gross_profit`, `operating_income`, `net_income`, `cost_of_goods_sold` |

| **Balance Sheet** | `total_assets`, `current_assets`, `inventory`, `cash`, `accounts_receivable`, `total_liabilities`, `current_liabilities`, `equity` |

| **Cash Flow** | `operating_cash_flow`, `interest_expense` |



## Analytical Ratios Included



- **Profitability**: Gross Margin, Operating Margin, Net Margin, ROA, ROE.
- 
- **Liquidity**: Current Ratio, Quick Ratio, Cash Ratio.
- 
- **Leverage**: Debt-to-Equity, Debt-to-Assets, Interest Coverage.
- 
- **Efficiency**: Asset Turnover, Inventory Turnover, Receivables Turnover.
- 


## License



This project is licensed under the MIT License.










