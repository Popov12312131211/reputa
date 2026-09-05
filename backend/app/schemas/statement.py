from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class StatementTransaction(BaseModel):
    date: date
    description: str
    # Знаковый: положительное — поступление, отрицательное — трата
    amount: Decimal
    category: str


class ParsedBankStatement(BaseModel):
    bank: str
    account_number: str | None = None
    period_start: date
    period_end: date
    opening_balance: Decimal
    closing_balance: Decimal
    income: Decimal
    expenses: Decimal
    expenses_by_category: dict[str, Decimal] = Field(default_factory=dict)
    transactions: list[StatementTransaction] = Field(default_factory=list)