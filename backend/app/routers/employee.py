from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.application import Application
from app.models.threshold_settings import ThresholdSettings
from app.models.user import User
from app.schemas.application import ApplicationListItemResponse
from app.schemas.threshold import ThresholdSettingsResponse, ThresholdSettingsUpdate
from app.services.auto_processing import get_threshold_settings

router = APIRouter(prefix="/employee", tags=["employee"])

# Доступ к /employee/* ограничен ролями middleware'om (main.py), который
# отдаёт 401 для не-сотрудников до попадания в любой роутер.


@router.get("/applications", response_model=list[ApplicationListItemResponse])
def list_all_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # EMP-004: таблица /employee/application показывает ВСЕ заявки всех
    # заёмщиков (в отличие от /user/applications), поэтому full_name берём
    # из связанной таблицы users. Новые сверху.
    applications = db.query(Application).order_by(Application.created_at.desc()).all()
    return [
        {
            "id": app.id,
            "user_id": app.user_id,
            "amount": app.amount,
            "purpose": app.purpose,
            "telegram": app.telegram,
            "telegram_channel": app.telegram_channel,
            "status": app.status,
            "score": app.score,
            "created_at": app.created_at,
            "full_name": app.user.full_name,
        }
        for app in applications
    ]


@router.get("/settings", response_model=ThresholdSettingsResponse)
def read_threshold_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_threshold_settings(db)


@router.put("/settings", response_model=ThresholdSettingsResponse)
def update_threshold_settings(
    body: ThresholdSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    settings: ThresholdSettings = get_threshold_settings(db)
    settings.auto_reject_threshold = body.auto_reject_threshold
    settings.auto_approve_threshold = body.auto_approve_threshold
    db.commit()
    db.refresh(settings)
    return settings