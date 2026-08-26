from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.fuzzy_neural import (
    fuzzy_credit_scoring,
    anfis_bankruptcy_prediction,
    fuzzy_rule_extraction,
    fuzzy_neural_demo,
)


router = APIRouter()


class CreditScoreRequest(BaseModel):
    income: float
    debt_ratio: float
    employment_years: float
    credit_history_months: float
    age: float


class BankruptcyPredictRequest(BaseModel):
    training_data: list[dict]
    test_data: list[dict]
    epochs: int = 50
    learning_rate: float = 0.01


class RuleExtractionRequest(BaseModel):
    data_matrix: list[list[float]]
    feature_names: list[str]
    n_clusters: int = 3
    output_column: int = -1


@router.post("/credit-score")
async def credit_score_endpoint(req: CreditScoreRequest):
    """Fuzzy inference credit scoring for a loan applicant."""
    applicant = req.model_dump()
    return fuzzy_credit_scoring(applicant)


@router.post("/bankruptcy-predict")
async def bankruptcy_predict_endpoint(req: BankruptcyPredictRequest):
    """ANFIS hybrid bankruptcy prediction with training and evaluation."""
    return anfis_bankruptcy_prediction(
        training_data=req.training_data,
        test_data=req.test_data,
        epochs=req.epochs,
        learning_rate=req.learning_rate,
    )


@router.post("/rule-extraction")
async def rule_extraction_endpoint(req: RuleExtractionRequest):
    """Extract interpretable fuzzy if-then rules from data via FCM clustering."""
    return fuzzy_rule_extraction(
        data_matrix=req.data_matrix,
        feature_names=req.feature_names,
        n_clusters=req.n_clusters,
        output_column=req.output_column,
    )


@router.get("/demo")
async def demo_endpoint():
    """Run full ANFIS Fuzzy Neural Engine demo with TSE-relevant data."""
    return fuzzy_neural_demo()
