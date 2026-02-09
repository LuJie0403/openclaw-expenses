
from pydantic import BaseModel
from typing import Optional, List

class ExpenseSummary(BaseModel):
    total_amount: float
    total_count: int
    avg_amount: float
    earliest_date: Optional[str]
    latest_date: Optional[str]

class MonthlyExpense(BaseModel):
    year: str
    month: str
    transaction_count: int
    monthly_total: float
    avg_transaction: float

class CategoryExpense(BaseModel):
    trans_type_name: Optional[str]
    trans_sub_type_name: Optional[str]
    count: int
    total_amount: float
    avg_amount: float

class PaymentMethod(BaseModel):
    pay_account: str
    usage_count: int
    total_spent: float
    avg_per_transaction: float

class TimelineData(BaseModel):
    date: str
    daily_total: float
    transaction_count: int
