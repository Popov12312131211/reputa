from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.threshold_settings import ThresholdSettings
from app.models.user import User
from app.schemas.threshold import ThresholdSettingsResponse, ThresholdSettingsUpdate
from app.services.auto_processing import get_threshold_settings

router = APIRouter(prefix="/employee", tags=["employee"])

# Доступ к /employee/* ограничен ролями middleware'om (main.py), который
# отдаёт 401 для не-сотрудников до попадания в любой роутер.


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