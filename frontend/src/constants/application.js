export const AMOUNT = {
  MIN: 1000,
  MAX: 10000000,
}

export const APPLICATION_STATUS = {
  IN_QUEUE: 'in_queue',
  AUTO_APPROVED: 'auto_approved',
  AUTO_REJECTED: 'auto_rejected',
  EMPLOYEE_APPROVED: 'employee_approved',
  EMPLOYEE_REJECTED: 'employee_rejected',
}

// Сгруппированы для UI: обработка / одобрено / отклонено
export const STATUS_GROUP = {
  [APPLICATION_STATUS.IN_QUEUE]: 'pending',
  [APPLICATION_STATUS.AUTO_APPROVED]: 'approved',
  [APPLICATION_STATUS.AUTO_REJECTED]: 'rejected',
  [APPLICATION_STATUS.EMPLOYEE_APPROVED]: 'approved',
  [APPLICATION_STATUS.EMPLOYEE_REJECTED]: 'rejected',
}