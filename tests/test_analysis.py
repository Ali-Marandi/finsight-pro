import tempfile
import unittest
from pathlib import Path

import pandas as pd

from finsight.io import load_statement
from finsight.ratios import calculate_ratios


DATA = {
    "period": ["2024", "2025"],
    "revenue": [1000, 1200],
    "gross_profit": [400, 540],
    "cost_of_goods_sold": [600, 660],
    "operating_income": [200, 264],
    "net_income": [120, 156],
    "total_assets": [2000, 2200],
    "current_assets": [800, 900],
    "inventory": [200, 240],
    "cash": [150, 180],
    "total_liabilities": [900, 950],
    "current_liabilities": [400, 450],
    "equity": [1100, 1250],
    "operating_cash_flow": [180, 210],
    "interest_expense": [40, 44],
    "accounts_receivable": [250, 280],
}


class AnalysisTests(unittest.TestCase):
    def test_ratios(self):
        ratios = calculate_ratios(pd.DataFrame(DATA))
        self.assertAlmostEqual(ratios.loc[0, "gross_margin"], 0.4)
        self.assertAlmostEqual(ratios.loc[0, "current_ratio"], 2)
        self.assertAlmostEqual(ratios.loc[1, "return_on_equity"], 156 / 1250)

    def test_csv_ingestion(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "statement.csv"
            pd.DataFrame(DATA).to_csv(path, index=False)
            loaded = load_statement(path)
            self.assertEqual(list(loaded["period"].astype(str)), ["2024", "2025"])

    def test_missing_column_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            pd.DataFrame({"period": ["2025"], "revenue": [100]}).to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "missing required columns"):
                load_statement(path)


if __name__ == "__main__":
    unittest.main()
