import numpy as np
import os

from app.scoring.stmt_parser import parse_statement
from app.scoring.stmt_scoring import score_statement, StatementScoringResult
from app.scoring.telegram_scoring import TelegramScoringResult
from app.scoring.telegram_channel import fetch_channel_messages
from app.scoring.telegram_llm import score_telegram_with_llm
from app.scoring.model_training import load_model_artifacts, predict_from_pdf


'''
Получает на вход сырые данные о клиенте, возвращает финальную оценку
'''
def process_raw_application(pdf_path: str, tg_username: str | None = None) -> dict:
    # 1
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Файл выписки не найден: {pdf_path}")
        
    with open(pdf_path, "rb") as f:
        parsed_stmt = parse_statement(f.read())
        
    stmt_result = score_statement(parsed_stmt)

    # 2
    loaded_model, loaded_scaler, loaded_cols = load_model_artifacts("artifacts")
    model_prediction = predict_from_pdf(pdf_path, loaded_model, loaded_scaler, loaded_cols)

    # 3
    tg_result = None
    if tg_username:
        channel_data = fetch_channel_messages(tg_username)
        if channel_data:
            tg_result = score_telegram_with_llm(channel_data)

    return calculate_final_profile(model_predsiction, stmt_result, tg_result)


"""
Объединяет результаты скоринга по выписке, предсказание модели и данные по Telegram-каналу.
"""
def calculate_final_profile(model_prediction: int,
    stmt_result: StatementScoringResult,
    tg_result: TelegramScoringResult | None = None
) -> dict:

    if not tg_result:
        return {
            "score": stmt_result["score"],
            "positive_signals": stmt_result["positive_signals"],
            "risk_factors": stmt_result["risk_factors"],
            "stability_score": stmt_result["stability_score"],
            "financial_literacy_score": stmt_result["financial_literacy_score"],
            "responsibility_score": stmt_result["responsibility_score"],
            "report_content": stmt_result["report_content"],
        }

    if not model_prediction:
        model_prediction = stmt_result["score"]

    final_score = int(np.clip(round(model_prediction * 0.7 + tg_result["score_contribution"] * 0.3), 0, 100))

    positive_signals = stmt_result["positive_signals"] + tg_result["positive_signals"]
    risk_factors = stmt_result["risk_factors"] + tg_result["risk_factors"]

    stability = int(np.clip(round((stmt_result["stability_score"] + tg_result["stability_score"]) / 2.0), 0, 10))
    fin_lit = int(np.clip(round((stmt_result["financial_literacy_score"] + tg_result["financial_literacy_score"]) / 2.0), 0, 10))
    resp = int(np.clip(round((stmt_result["responsibility_score"] + tg_result["responsibility_score"]) / 2.0), 0, 10))

    report_content = f"{stmt_result['report_content']}\n\n{tg_result['report_content']}"

    return {
        "score": final_score,
        "positive_signals": positive_signals,
        "risk_factors": risk_factors,
        "stability_score": stability,
        "financial_literacy_score": fin_lit,
        "responsibility_score": resp,
        "report_content": report_content,
    }