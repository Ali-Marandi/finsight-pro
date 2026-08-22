import io
import sys
import unittest
from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).parents[1]
API_ROOT = PROJECT_ROOT / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.routers.evidence import router


STATEMENT = {
    "period": ["2025"],
    "revenue": [1_200],
    "gross_profit": [540],
    "operating_income": [264],
    "net_income": [156],
    "total_assets": [2_200],
    "current_assets": [900],
    "inventory": [240],
    "cash": [180],
    "total_liabilities": [950],
    "current_liabilities": [450],
    "equity": [1_250],
    "operating_cash_flow": [210],
    "interest_expense": [44],
    "cost_of_goods_sold": [660],
    "accounts_receivable": [150],
}


class EvidenceApiTests(unittest.TestCase):
    def test_inspection_returns_reviewable_health_payload(self):
        app = FastAPI()
        app.include_router(router, prefix="/api/v1/evidence")
        stream = io.StringIO()
        pd.DataFrame(STATEMENT).to_csv(stream, index=False)

        response = TestClient(app).post(
            "/api/v1/evidence/inspect",
            files={"file": ("client_statement.csv", stream.getvalue(), "text/csv")},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ready_for_analysis"])
        self.assertEqual(payload["manifest"]["file_name"], "client_statement.csv")
        self.assertEqual(payload["health"]["blocking"], 0)


if __name__ == "__main__":
    unittest.main()
