from sqlalchemy.orm import Session

from app.core.constants import (
    APPLICATION_STATUS_AUTO_APPROVED,
    APPLICATION_STATUS_AUTO_REJECTED,
    APPLICATION_STATUS_IN_QUEUE,
    AUTO_APPROVE_THRESHOLD_DEFAULT,
    AUTO_REJECT_THRESHOLD_DEFAULT,
    THRESHOLD_SETTINGS_ID,
)
from app.models.application import Application
from app.models.threshold_settings import ThresholdSettings


def get_threshold_settings(db: Session) -> ThresholdSettings:
    """Возвращает настройки порогов (синглтон). Если строки нет — создаёт с дефолтами
    (страховка для пустой БД; в норме строку сидирует миграция 0004)."""
    settings = db.query(ThresholdSettings).filter(ThresholdSettings.id == THRESHOLD_SETTINGS_ID).first()
    if settings is None:
        settings = ThresholdSettings(
            id=THRESHOLD_SETTINGS_ID,
            auto_reject_threshold=AUTO_REJECT_THRESHOLD_DEFAULT,
            auto_approve_threshold=AUTO_APPROVE_THRESHOLD_DEFAULT,
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def decide_auto_status(score: int, settings: ThresholdSettings) -> str:
    """Чистая функция принятия решения по итоговой оценке (APP-003).

    score ≤ порога авто-отклонения → auto_rejected;
    score ≥ порога авто-одобрения → auto_approved;
    иначе заявка уходит в очередь сотрудника (in_queue).
    """
    if score <= settings.auto_reject_threshold:
        return APPLICATION_STATUS_AUTO_REJECTED
    if score >= settings.auto_approve_threshold:
        return APPLICATION_STATUS_AUTO_APPROVED
    return APPLICATION_STATUS_IN_QUEUE


def apply_auto_decision(db: Session, application: Application) -> str | None:
    """Применяет автообработку к заявке после расчёта итоговой оценки.

    Вызывается из пайплайна скоринга (STMT-002/TG-003). Без оценки (score is None)
    статус не меняется и возвращается None.
    """
    if application.score is None:
        return None
    status = decide_auto_status(
        application.score, get_threshold_settings(db)
    )
    application.status = status
    db.commit()
    return status