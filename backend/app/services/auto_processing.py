import random
from typing import Sequence

from sqlalchemy.orm import Session

from app.core.constants import (
    APPLICATION_STATUS_AUTO_APPROVED,
    APPLICATION_STATUS_AUTO_REJECTED,
    APPLICATION_STATUS_IN_QUEUE,
    AUTO_APPROVE_THRESHOLD_DEFAULT,
    AUTO_REJECT_THRESHOLD_DEFAULT,
    ROLE_EMPLOYEE,
)
from app.models.application import Application
from app.models.employee_thresholds import EmployeeThresholds
from app.models.user import User


def get_employee_thresholds(
    db: Session, employee: User, *, commit: bool = True
) -> EmployeeThresholds:
    """Возвращает персональные пороги сотрудника (APP-008).

    Если записи нет — создаёт с дефолтами (страховка для пустой БД; в норме
    записи сотрудников сидирует миграция 0006). `commit=False` используется
    вызывающим транзакционным пайплайном.
    """
    settings = (
        db.query(EmployeeThresholds)
        .filter(EmployeeThresholds.user_id == employee.id)
        .first()
    )
    if settings is None:
        settings = EmployeeThresholds(
            user_id=employee.id,
            auto_reject_threshold=AUTO_REJECT_THRESHOLD_DEFAULT,
            auto_approve_threshold=AUTO_APPROVE_THRESHOLD_DEFAULT,
        )
        db.add(settings)
        db.flush()
        if commit:
            db.commit()
            db.refresh(settings)
    return settings


def decide_auto_status(score: int, settings: EmployeeThresholds) -> str:
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


def _random_employees(db: Session, rng=random) -> Sequence[User]:
    """Случайный порядок сотрудников для перебора при автообработке.

    `.all()` и так возвращает новый список — тасуем только его. `rng`
    принимает любой объект с методом `shuffle` (для тестов — стаб).
    """
    employees = (
        db.query(User).filter(User.role == ROLE_EMPLOYEE).order_by(User.id).all()
    )
    rng.shuffle(employees)
    return employees


def apply_auto_decision(
    db: Session, application: Application, rng=random, *, commit: bool = True
) -> str | None:
    """Применяет автообработку к заявке после расчёта итоговой оценки (APP-008).

    Перебирает сотрудников в случайном порядке и проверяет, подпадает ли
    итоговая оценка под персональные пороги очередного сотрудника:
    - подпадает — заявка закрывается автоматически, а `decided_by` фиксирует
      сотрудника, закрывшего сделку;
    - не подпадает — следующий случайный сотрудник;
    - не подошёл ни один — заявка остаётся в очереди (in_queue), `decided_by`
      сбрасывается (не должно остаться stale-значение от прошлого прогона).

    Уже решённые заявки (статус не in_queue) не трогаются — возвращается
    текущий статус. Без оценки (score is None) статус не меняется
    и возвращается None. При `commit=False` изменения остаются в транзакции
    вызывающего кода.
    """
    if application.score is None:
        return None
    if application.status != APPLICATION_STATUS_IN_QUEUE:
        return application.status
    for employee in _random_employees(db, rng=rng):
        status = decide_auto_status(
            application.score, get_employee_thresholds(db, employee, commit=commit)
        )
        if status != APPLICATION_STATUS_IN_QUEUE:
            application.status = status
            application.decided_by = employee.id
            if commit:
                db.commit()
            return status
    application.status = APPLICATION_STATUS_IN_QUEUE
    application.decided_by = None
    if commit:
        db.commit()
    return APPLICATION_STATUS_IN_QUEUE
