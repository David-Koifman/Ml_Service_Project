from datetime import datetime
from pydantic import BaseModel


class MLModelOut(BaseModel):
    id: int
    name: str
    description: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PredictionRequest(BaseModel):
    person_age: float
    person_gender: str
    person_education: str
    person_income: float
    person_emp_exp: float
    person_home_ownership: str
    loan_amnt: float
    loan_intent: str
    loan_int_rate: float
    loan_percent_income: float
    cb_person_cred_hist_length: float
    credit_score: int
    previous_loan_defaults_on_file: str


class PredictionTaskOut(BaseModel):
    id: int
    model_id: int
    status: str
    input_data: dict
    result: dict | None
    credits_cost: int
    created_at: datetime

    model_config = {"from_attributes": True}
