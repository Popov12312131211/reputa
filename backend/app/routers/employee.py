from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.constants import MSG_APPLICATION_NOT_FOUND
from app.db.session import get_db
from app.models.application import Application
from app.models.employee_thresholds import EmployeeThresholds
from app.models.user import User
from app.schemas.application import (
    ApplicationListItemResponse,
    EmployeeApplicationDetailResponse,
)
from app.schemas.threshold import ThresholdSettingsResponse, ThresholdSettingsUpdate
from app.services.auto_processing import get_employee_thresholds

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


@router.get("/applications/{application_id}", response_model=EmployeeApplicationDetailResponse)
def get_application_detail(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # EMP-005: детальная карточка заявки сотрудника. В отличие от user-версии
    # (проверка принадлежности, /user/applications) сотруднику видна любая заявка
    # всех заёмщиков, поэтому фильтруем только по id; несуществующая — 404.
    # Полный разбор скоринга (score_result) отдаётся вместе с карточкой; пока
    # пайплайн STMT-002/TG-003 не заполнил результат, поле равно null.
    application = db.query(Application).filter(Application.id == application_id).first()
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MSG_APPLICATION_NOT_FOUND,
        )
    return {
        "id": application.id,
        "user_id": application.user_id,
        "amount": application.amount,
        "purpose": application.purpose,
        "telegram": application.telegram,
        "telegram_channel": application.telegram_channel,
        "status": application.status,
        "score": application.score,
        "created_at": application.created_at,
        "full_name": application.user.full_name,
        "score_result": application.score_result,
        "decided_by_employee": application.decided_by_user,
    }


@router.get("/settings", response_model=ThresholdSettingsResponse)
def read_threshold_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # EMP-002/APP-008: пороги персональные — читаем настройки текущего сотрудника.
    return get_employee_thresholds(db, current_user)


@router.put("/settings", response_model=ThresholdSettingsResponse)
def update_threshold_settings(
    body: ThresholdSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    settings: EmployeeThresholds = get_employee_thresholds(db, current_user)
    settings.auto_reject_threshold = body.auto_reject_threshold
    settings.auto_approve_threshold = body.auto_approve_threshold
    db.commit()
    db.refresh(settings)
    return settings