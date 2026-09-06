from decimal import Decimal
from datetime import date
from typing import TypedDict
import numpy as np

from app.core.constants import (
    STMT_CATEGORY_GROCERIES,
    STMT_CATEGORY_UTILITIES,
    STMT_CATEGORY_HEALTH,
    STMT_CATEGORY_TRANSPORT,
    STMT_CATEGORY_CAFES,
    STMT_CATEGORY_SHOPPING,
)
from app.schemas.statement import ParsedBankStatement

class StatementScoringResult(TypedDict):
    score: int
    positive_signals: list[str]
    risk_factors: list[str]
    stability_score: int
    financial_literacy_score: int
    responsibility_score: int
    report_content: str

'''
Функция из обработанной банковской выписки извлекает фичи для обучения.
'''
def calculate_statement_features(statement: ParsedBankStatement) -> dict[str, float]:

    income = float(statement.income)
    expenses = float(statement.expenses)
    closing_bal = float(statement.closing_balance)

    # 1. Отношение доходов к расходам
    cashflow_ratio = income / max(expenses, 1.0)

    # 2. Доли категорий расходов
    cat_exp = {k: float(v) for k, v in statement.expenses_by_category.items()}
    
    # (необходимые затраты - еда, жкх, интернет, здоровье, транспорт и т.д.)
    essential_exp = (
        cat_exp.get(STMT_CATEGORY_GROCERIES, 0.0)
        + cat_exp.get(STMT_CATEGORY_UTILITIES, 0.0)
        + cat_exp.get(STMT_CATEGORY_HEALTH, 0.0)
        + cat_exp.get(STMT_CATEGORY_TRANSPORT, 0.0)
    )
    essential_ratio = essential_exp / max(expenses, 1.0)

    # (дополнительные затраты - кафе, рестораны, шоппинг, развлечния и т.д.)
    discretionary_exp = (
        cat_exp.get(STMT_CATEGORY_CAFES, 0.0)
        + cat_exp.get(STMT_CATEGORY_SHOPPING, 0.0)
    )
    discretionary_ratio = discretionary_exp / max(expenses, 1.0)

    # 3. Анализ частоты и регулярности поступлений
    income_txs = [tx for tx in statement.transactions if tx.amount > 0]
    num_incomes = len(income_txs)
    
    # Средний интервал между пополнениями (в днях)
    if num_incomes >= 2:
        income_dates = sorted([tx.date for tx in income_txs])
        intervals = [(income_dates[i] - income_dates[i - 1]).days for i in range(1, len(income_dates))]
        avg_income_interval = float(np.mean(intervals))
        income_interval_std = float(np.std(intervals))
    else:
        avg_income_interval = 30.0
        income_interval_std = 15.0

    # 4. Подушка безопасности относительно месячного расхода
    period_days = max(1, (statement.period_end - statement.period_start).days) if statement.period_start and statement.period_end else 90
    monthly_expense = expenses / (period_days / 30.0)
    cushion_ratio = closing_bal / max(monthly_expense, 1.0)

    return {
        "income": income,
        "expenses": expenses,
        "cashflow_ratio": cashflow_ratio,
        "essential_ratio": essential_ratio,
        "discretionary_ratio": discretionary_ratio,
        "num_incomes": num_incomes,
        "avg_income_interval": avg_income_interval,
        "income_interval_std": income_interval_std,
        "cushion_ratio": cushion_ratio,
    }



def score_statement(statement: ParsedBankStatement) -> StatementScoringResult:
    feats = calculate_statement_features(statement)
    positive_signals = []
    risk_factors = []
    
    # Базовый балл
    raw_score = 50.0

    cfr = feats["cashflow_ratio"]
    if cfr >= 1.30:
        raw_score += 25.0
        positive_signals.append("Крупный профицит: доходы стабильно и значительно превышают расходы.")
    elif 1.05 <= cfr < 1.30:
        raw_score += 12.0
        positive_signals.append("Положительный баланс: клиент тратит меньше, чем зарабатывает.")
    elif 0.95 <= cfr < 1.05:
        risk_factors.append("Бюджет 'в ноль': накопления практически не формируются.")
    else:
        raw_score -= 20.0
        risk_factors.append("Хронический дефицит: расходы превышают регулярные поступления.")

    ess = feats["essential_ratio"]
    if 0.30 <= ess <= 0.65:
        raw_score += 10.0
        positive_signals.append("Сбалансированная структура трат на базовые жизненные нужды.")
    elif ess > 0.85:
        raw_score -= 15.0
        risk_factors.append("Критическая доля базовых расходов: высокий риск потери платежеспособности.")

    disc = feats["discretionary_ratio"]
    if disc > 0.35 and cfr < 1.10:
        raw_score -= 15.0
        risk_factors.append("Высокие траты на развлечения при отсутствии существенного профицита бюджета.")
    elif disc < 0.20:
        raw_score += 5.0
        positive_signals.append("Строгий контроль необязательных расходов.")

    if feats["num_incomes"] >= 3:
        if feats["income_interval_std"] < 7.0:
            raw_score += 15.0
            positive_signals.append("Идеальная ритмичность поступлений (минимальный разброс в датах).")
        elif feats["income_interval_std"] < 15.0:
            raw_score += 5.0
    else:
        raw_score -= 15.0
        risk_factors.append("Нерегулярный, разовый или нестабильный характер доходов.")

    cush = feats["cushion_ratio"]
    if cush >= 1.0:
        raw_score += 15.0
        positive_signals.append("Надежная финансовая подушка (остатка хватит более чем на месяц расходов).")
    elif cush >= 0.3:
        raw_score += 5.0
    else:
        raw_score -= 10.0
        risk_factors.append("Отсутствие ликвидного резерва на конец периода.")

    final_score = int(np.clip(round(raw_score), 0, 100))

    stability_score = int(np.clip(round((min(cfr, 1.5) / 1.5) * 5.0 + (10.0 / max(feats["income_interval_std"], 1.0)) * 5.0), 0, 10))
    financial_literacy_score = int(np.clip(round((1.0 - min(disc, 1.0)) * 5.0 + min(cush, 1.0) * 5.0), 0, 10))
    responsibility_score = int(np.clip(round((final_score / 100.0) * 7.0 + (3.0 if not risk_factors else 0.0)), 0, 10))

    report_content = (
        f"Анализ транзакций: Доходы {feats['income']:,.0f} руб., Расходы {feats['expenses']:,.0f} руб. "
        f"Коэффициент покрытия: {cfr:.2f}. Средний интервал доходов: {feats['avg_income_interval']:.1f} дн. "
        f"Текущий остаток покрывает {cush:.2f} мес. расходов. Итог алгоритма: {final_score}/100."
    )

    return {
        "score": final_score,
        "positive_signals": positive_signals,
        "risk_factors": risk_factors,
        "stability_score": stability_score,
        "financial_literacy_score": financial_literacy_score,
        "responsibility_score": responsibility_score,
        "report_content": report_content,
    }


'''
Локальная проверка получения оценок для сырых файлов

if __name__ == "__main__":
    import json
    import os
    from app.scoring.stmt_parser import parse_statement

    names = ["Выписка", "Выписка (1)", "Выписка (2)", "funds_movement", "выписка по счету альфа", "Выписка по счёту дебетовой карты", "AM_1788587469194pdf", "Баглаева_А_А_о_движении_денежных_средств_ozonbank_document_35151989"]
    for name in names:
        pdf_path = "C:/Users/maxto/Downloads/" + name + ".pdf"
    
    
        with open(pdf_path, "rb") as f:
            parsed_stmt = parse_statement(f.read())
            
        features = calculate_statement_features(parsed_stmt)
        result = score_statement(parsed_stmt)
        
        print(name, result["score"])
'''