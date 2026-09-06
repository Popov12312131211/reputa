from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.constants import MSG_APPLICATION_NOT_FOUND
from app.db.session import get_db
from app.models.application import Application
from app.models.user import User
from app.schemas.application import ApplicationDetailResponse, ApplicationResponse

# Роутер заявок пользователя (APP-004/APP-005). Префикс /user/ уже защищён
# middleware-ом (main.py) для роли "user", здесь дополнительно убеждаемся,
# что заявка принадлежит именно текущему авторизованному пользователю.
router = APIRouter(prefix="/user/applications", tags=["user applications"])


@router.get("", response_model=list[ApplicationResponse])
def list_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # APP-004: таблица /user/my показывает только заявки текущего пользователя,
    # новые сверху. Детальные поля (full_name/purpose) в списке не нужны —
    # их отдаёт GET /user/applications/{application_id} для карточки (APP-005).
    return (
        db.query(Application)
        .filter(Application.user_id == current_user.id)
        .order_by(Application.created_at.desc())
        .all()
    )


@router.get("/{application_id}", response_model=ApplicationDetailResponse)
def get_application(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Фильтр по и по id, и по user_id: чужая заявка просто «не находится» (404),
    # что не раскрывает факт её существования и служит той же защитой, что и 403.
    application = (
        db.query(Application)
        .filter(
            Application.id == application_id,
            Application.user_id == current_user.id,
        )
        .first()
    )
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
        "full_name": current_user.full_name,
    }
