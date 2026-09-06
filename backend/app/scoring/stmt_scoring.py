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



def calculate_score_from_features(feats: dict[str, float]) -> dict:
    """
    Универсальная функция начисления баллов. 
    Принимает готовый словарь признаков, возвращает итоговый скор и отчет.
    """
    positive_signals: list[str] = []
    risk_factors: list[str] = []
    raw_score = 50.0

    # 1. Денежный поток (cashflow_ratio). Влияние: от -25 до +20
    cfr = feats["cashflow_ratio"]
    if cfr >= 1.20:
        raw_score += 20.0
        positive_signals.append("Уверенный профицит: доходы превышают расходы более чем на 20%.")
    elif 1.05 <= cfr < 1.20:
        raw_score += 10.0
        positive_signals.append("Положительный баланс: траты меньше заработка.")
    elif 0.95 <= cfr < 1.05:
        raw_score -= 10.0
        risk_factors.append("Бюджет 'в ноль': отсутствие формирования капитала.")
    else:
        raw_score -= 25.0
        risk_factors.append("Дефицит бюджета: расходы стабильно превышают доходы.")

    # 2. Финансовая подушка (cushion_ratio). Влияние: от -20 до +15
    cush = feats["cushion_ratio"]
    if cush >= 1.0:
        raw_score += 15.0
        positive_signals.append("Надежная подушка безопасности (хватит более чем на месяц).")
    elif cush >= 0.3:
        raw_score += 5.0
    elif cush < 0.1:
        raw_score -= 20.0
        risk_factors.append("Критически низкий или нулевой остаток на конец периода.")
    else:
        raw_score -= 10.0
        risk_factors.append("Отсутствие достаточного ликвидного резерва.")

    # 3. Базовые потребности (essential_ratio). Влияние: от -15 до +10
    ess = feats["essential_ratio"]
    if 0.30 <= ess <= 0.65:
        raw_score += 10.0
        positive_signals.append("Сбалансированная доля расходов на базовые нужды.")
    elif ess > 0.85:
        raw_score -= 15.0
        risk_factors.append("Критическая доля базовых трат: высокий риск при падении доходов.")

    # 4. Развлечения (discretionary_ratio). Влияние: от -15 до +10
    disc = feats["discretionary_ratio"]
    if disc > 0.40:
        raw_score -= 15.0
        risk_factors.append("Чрезмерные траты на развлечения и необязательные покупки.")
    elif disc < 0.20:
        raw_score += 10.0
        positive_signals.append("Разумный контроль необязательных расходов.")

    # 5. Регулярность доходов. Влияние: от -20 до +15
    num_inc = feats["num_incomes"]
    std = feats["income_interval_std"]
    avg_int = feats["avg_income_interval"]

    if num_inc < 2:
        raw_score -= 20.0
        risk_factors.append("Разовый или нерегулярный характер доходов (менее 2 поступлений).")
    else:
        if std < 7.0 and 10.0 <= avg_int <= 35.0:
            raw_score += 15.0
            positive_signals.append("Стабильные регулярные поступления (зарплатный паттерн).")
        elif std < 15.0:
            raw_score += 5.0
        elif avg_int < 10.0 and std > 10.0:
            raw_score -= 10.0
            risk_factors.append("Хаотичные частые поступления (возможна нестабильная занятость).")

    final_score = int(np.clip(round(raw_score), 0, 100))

    stability_score = int(np.clip(round((min(cfr, 1.5) / 1.5) * 5.0 + (10.0 / max(std, 1.0)) * 5.0), 0, 10))
    financial_literacy_score = int(np.clip(round((1.0 - min(disc, 1.0)) * 5.0 + min(cush, 1.0) * 5.0), 0, 10))
    responsibility_score = int(np.clip(round((final_score / 100.0) * 7.0 + (3.0 if not risk_factors else 0.0)), 0, 10))

    report_content = (
        f"Анализ транзакций: Доходы {feats['income']:,.0f} руб., Расходы {feats['expenses']:,.0f} руб. "
        f"Коэффициент покрытия: {cfr:.2f}. Средний интервал доходов: {avg_int:.1f} дн. "
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


def score_statement(statement: ParsedBankStatement) -> StatementScoringResult:
    feats = calculate_statement_features(statement)
    return calculate_score_from_features(feats)



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