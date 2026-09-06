from decimal import Decimal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_current_employee, get_current_user
from app.core.constants import (
    MSG_APPLICATION_ALREADY_DECIDED,
    MSG_APPLICATION_NOT_FOUND,
    MSG_STATEMENT_TOO_LARGE,
    MSG_STATEMENT_UNPARSABLE,
    STATEMENT_MAX_SIZE_BYTES,
)
from app.db.session import get_db
from app.models.application import Application, ApplicationStatus
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationDecision,
    ApplicationDecisionRequest,
    ApplicationResponse,
)
from app.scoring.stmt_parser import StatementParseError, parse_statement

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    amount: Decimal = Form(...),
    purpose: str = Form(...),
    telegram: str = Form(...),
    telegram_channel: str = Form(""),
    statement: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        data = ApplicationCreate(
            amount=amount,
            purpose=purpose,
            telegram=telegram,
            telegram_channel=telegram_channel,
        )
    except ValidationError as exc:
        # Валидация Form-полей выполняется явно, поэтому ошибки схемы
        # приводим к тому же виду 422, что и у body-эндпоинтов (auth).
        # `input` отбрасывается: исходное значение может быть несериализуемым (Decimal).
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=jsonable_encoder(exc.errors(include_input=False)),
        ) from exc

    statement_content = await statement.read()
    if len(statement_content) > STATEMENT_MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=MSG_STATEMENT_TOO_LARGE,
        )

    # STMT-001: выписка разбирается на данные (остаток, поступления, траты).
    # Файл нигде не сохраняется (см. PLAN.md), распознавание служит валидацией
    # того, что загружен именно файл-выписка поддерживаемого банка.
    try:
        parse_statement(statement_content, filename=statement.filename)
    except StatementParseError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=MSG_STATEMENT_UNPARSABLE,
        ) from None

    application = Application(
        user_id=current_user.id,
        amount=data.amount,
        purpose=data.purpose,
        telegram=data.telegram,
        telegram_channel=data.telegram_channel,
        status=ApplicationStatus.IN_QUEUE.value,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


@router.post("/{application_id}/decision", response_model=ApplicationResponse)
def decide_application(
    application_id: int,
    body: ApplicationDecisionRequest,
    db: Session = Depends(get_db),
    current_employee: User = Depends(get_current_employee),
):
    application = db.query(Application).filter(Application.id == application_id).first()
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=MSG_APPLICATION_NOT_FOUND,
        )
    if application.status != ApplicationStatus.IN_QUEUE.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=MSG_APPLICATION_ALREADY_DECIDED,
        )

    application.status = (
        ApplicationStatus.EMPLOYEE_APPROVED.value
        if body.decision == ApplicationDecision.APPROVE
        else ApplicationStatus.EMPLOYEE_REJECTED.value
    )
    db.commit()
    db.refresh(application)
    return application