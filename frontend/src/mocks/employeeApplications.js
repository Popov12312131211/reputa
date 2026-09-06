import { APPLICATION_STATUS } from '../constants/application'

// Единый источник mock-заявок кабинета сотрудника (EMP-003 / EMP-004 / EMP-005).
// Старые инлайн-заглушки в компонентах удалены; все данные живут только здесь.
//
// Статусы заявки — литеральные значения ровно одного из трёх видов:
//   'pending'  — на рассмотрении (очередь сотрудника),
//   'approved' — одобрено,
//   'rejected' — отклонено.
//
// Структура каждой записи описывает поля обновлённого UI:
//   id, full_name, amount                        — идентификатор и заёмщик,
//   status                                       — статус (pending/approved/rejected),
//   purpose                                      — цель кредита,
//   positive_signals, risk_factors               — позитивные сигналы и факторы риска,
//   portrait                                     — психологический портрет 0–10
//                                                 (stability / financial_literacy / responsibility),
//   report                                       — отчёт комитета: путь к файлу + история
//                                                 скачиваний [{ date, id }],
//   score                                        — итоговая оценка 0–100 (спидометр),
//   decided_by                                   — данные об обработке: для 'pending' — null,
//                                                 для 'approved'/'rejected' — { full_name, login,
//                                                 decided_at }.
export const mockApplications = [
  {
    id: '3F9A2C7D1E',
    full_name: 'Иванов Иван Иванович',
    amount: 250000,
    status: 'pending',
    purpose: 'На корм для уток',
    created_at: '2026-09-05T10:12:00Z',
    positive_signals: [
      'Регулярные поступления на счёт без пропусков за полгода',
      'Доля обязательных трат не превышает 40% дохода',
      'Стабильный остаток на счёте на конец месяца',
    ],
    risk_factors: [
      'Крупное разовое списание за последний месяц без пояснения',
    ],
    portrait: { stability: 9, financial_literacy: 6, responsibility: 8 },
    score: 84,
    report: {
      path: 'reports/3F9A2C7D1E.txt',
      updated_at: '2026-09-05T09:12:00Z',
      downloads: [
        { date: '2026-09-04T12:40:00Z', id: 'ID1029391923' },
        { date: '2026-09-05T09:15:00Z', id: 'ID8374417265' },
      ],
    },
    decided_by: null,
  },
  {
    id: '8B4D0E5F2A',
    full_name: 'Петрова Анна Сергеевна',
    amount: 150000,
    status: 'pending',
    purpose: 'Ремонт квартиры',
    created_at: '2026-09-05T09:40:00Z',
    positive_signals: [
      'Поступления от работодателя равными суммами раз в две недели',
      'Траты преимущественно на товары первой необходимости',
    ],
    risk_factors: [
      'Просрочки по платежам за последние 6 месяцев',
      'Остаток на счёте на конец месяца близок к нулю',
    ],
    portrait: { stability: 6, financial_literacy: 4, responsibility: 5 },
    score: 41,
    report: {
      path: 'reports/8B4D0E5F2A.txt',
      updated_at: '2026-09-05T09:38:00Z',
      downloads: [],
    },
    decided_by: null,
  },
  {
    id: '1C6A9B3D84',
    full_name: 'Сидоров Пётр Алексеевич',
    amount: 500000,
    status: 'pending',
    purpose: 'Покупка автомобиля',
    created_at: '2026-09-04T18:05:00Z',
    positive_signals: [
      'Стабильный доход от основной занятости',
      'Предыдущий кредит погашен без просрочек',
      'Активности в азартных играх не выявлено',
    ],
    risk_factors: [
      'Единичные операции в букмекерских приложениях',
      'Несколько крупных списаний без явно выраженной цели',
    ],
    portrait: { stability: 8, financial_literacy: 7, responsibility: 8 },
    score: 66,
    report: {
      path: 'reports/1C6A9B3D84.txt',
      updated_at: '2026-09-04T18:02:00Z',
      downloads: [
        { date: '2026-09-03T16:05:00Z', id: 'ID2048165392' },
      ],
    },
    decided_by: null,
  },
  {
    id: '9A2C4F7E1D',
    full_name: 'Волкова Екатерина Павловна',
    amount: 300000,
    status: 'pending',
    purpose: 'Открытие кофейни',
    created_at: '2026-09-03T09:15:00Z',
    positive_signals: [
      'Поступления из нескольких независимых источников',
      'Регулярные траты на образование и развитие',
    ],
    risk_factors: [
      'Нет подтверждённого трудового стажа за последний год',
      'Доля личного потребления превышает 70% дохода',
    ],
    portrait: { stability: 4, financial_literacy: 8, responsibility: 7 },
    score: 52,
    report: {
      path: 'reports/9A2C4F7E1D.txt',
      updated_at: '2026-09-03T09:13:00Z',
      downloads: [],
    },
    decided_by: null,
  },
  {
    id: 'E2F7C4A09B',
    full_name: 'Кузнецова Мария Дмитриевна',
    amount: 75000,
    status: 'approved',
    purpose: 'Курсы по успешному успеху',
    created_at: '2026-09-04T14:27:00Z',
    positive_signals: [
      'Стабильные поступления на счёт каждый месяц',
      'Положительная кредитная история без просрочек',
      'Средний балл портрета выше отраслевого',
    ],
    risk_factors: [
      'Высокая доля трат на развлечения и досуг',
    ],
    portrait: { stability: 8, financial_literacy: 7, responsibility: 9 },
    score: 77,
    report: {
      path: 'reports/E2F7C4A09B.txt',
      updated_at: '2026-09-04T14:20:00Z',
      downloads: [
        { date: '2026-09-04T11:20:00Z', id: 'ID5920481753' },
      ],
    },
    decided_by: {
      full_name: 'Смирнов Алексей Владимирович',
      login: 'a.smirnov',
      decided_at: '2026-09-05T15:30:00Z',
    },
  },
  {
    id: '5D8E1F6B30',
    full_name: 'Орлова Светлана Викторовна',
    amount: 420000,
    status: 'approved',
    purpose: 'Покупка квартиры',
    created_at: '2026-09-04T11:05:00Z',
    positive_signals: [
      'Длительный трудовой стаж без перерывов',
      'Стабильно высокий остаток на счёте',
      'Регулярные сбережения на отдельных счетах',
    ],
    risk_factors: [],
    portrait: { stability: 10, financial_literacy: 7, responsibility: 8 },
    score: 88,
    report: {
      path: 'reports/5D8E1F6B30.txt',
      updated_at: '2026-09-04T10:00:00Z',
      downloads: [
        { date: '2026-09-04T10:00:00Z', id: 'ID7729310458' },
        { date: '2026-09-04T14:12:00Z', id: 'ID3301762849' },
      ],
    },
    decided_by: {
      full_name: 'Петрова Елена Сергеевна',
      login: 'petrova_e',
      decided_at: '2026-09-04T17:45:00Z',
    },
  },
  {
    id: '8C1A7B2E93',
    full_name: 'Смирнов Алексей Николаевич',
    amount: 1000000,
    status: 'rejected',
    purpose: 'Погашение долгов',
    created_at: '2026-09-03T11:50:00Z',
    positive_signals: [],
    risk_factors: [
      'Многократные просрочки по платежам за последний год',
      'Погашение действующей задолженности новыми кредитами',
      'Активность в микрофинансовых организациях',
    ],
    portrait: { stability: 3, financial_literacy: 4, responsibility: 2 },
    score: 12,
    report: {
      path: 'reports/8C1A7B2E93.txt',
      updated_at: '2026-09-03T11:50:00Z',
      downloads: [
        { date: '2026-09-03T11:48:00Z', id: 'ID9012846520' },
      ],
    },
    decided_by: {
      full_name: 'Волков Алексей Петрович',
      login: 'volkov_a',
      decided_at: '2026-09-03T13:20:00Z',
    },
  },
  {
    id: '4D6F8A2C50',
    full_name: 'Козлов Дмитрий Андреевич',
    amount: 200000,
    status: 'rejected',
    purpose: 'Ремонт техники',
    created_at: '2026-09-05T10:50:00Z',
    positive_signals: [
      'Регулярные поступления от работодателя',
    ],
    risk_factors: [
      'Высокая активность в азартных играх (более 15% дохода)',
      'Просрочки более 30 дней в отчётном периоде',
    ],
    portrait: { stability: 5, financial_literacy: 3, responsibility: 4 },
    score: 29,
    report: {
      path: 'reports/4D6F8A2C50.txt',
      updated_at: '2026-09-05T10:58:00Z',
      downloads: [],
    },
    decided_by: {
      full_name: 'Волков Алексей Петрович',
      login: 'volkov_a',
      decided_at: '2026-09-05T11:05:00Z',
    },
  },
]

// Литеральные статусы из mockApplications → статусы Application из constants.
const STATUS_TO_APPLICATION_STATUS = {
  pending: APPLICATION_STATUS.IN_QUEUE,
  approved: APPLICATION_STATUS.EMPLOYEE_APPROVED,
  rejected: APPLICATION_STATUS.EMPLOYEE_REJECTED,
}

// Текст отчёта комитета для .txt-выгрузки собирается из полей mock-заявки —
// чтобы «Скачать отчёт для банка» работало на тех же данных, что и UI.
function buildReportContent(mock) {
  const rows = []
  rows.push(`Отчёт кредитного комитета по заявке ${mock.id}`)
  rows.push('')
  rows.push(`Заёмщик: ${mock.full_name}`)
  rows.push(`Запрашиваемая сумма: ${Number(mock.amount).toLocaleString('ru-RU')} ₽`)
  rows.push(`Цель кредита: ${mock.purpose}`)
  rows.push('')
  rows.push('Позитивные сигналы:')
  if (mock.positive_signals.length > 0) {
    for (const signal of mock.positive_signals) rows.push(`- ${signal}`)
  } else {
    rows.push('- Не выявлено')
  }
  rows.push('')
  rows.push('Факторы риска:')
  if (mock.risk_factors.length > 0) {
    for (const factor of mock.risk_factors) rows.push(`- ${factor}`)
  } else {
    rows.push('- Не выявлено')
  }
  rows.push('')
  const portrait = mock.portrait || {}
  rows.push('Психологический портрет:')
  rows.push(`- Стабильность работы: ${portrait.stability != null ? portrait.stability : 0}/10`)
  rows.push(`- Финансовая грамотность: ${portrait.financial_literacy != null ? portrait.financial_literacy : 0}/10`)
  rows.push(`- Ответственность: ${portrait.responsibility != null ? portrait.responsibility : 0}/10`)
  rows.push('')
  rows.push(`Итоговая оценка благонадёжности: ${mock.score} из 100.`)
  return rows.join('\n')
}

// Приводит запись из mockApplications к виду, который ожидает UI/API-ответ
// (тот же формат, что GET /employee/applications: snake_case, статусы
// Application, score_result, decided_by_employee/decided_at, downloads).
export function toEmployeeApplication(mock) {
  const report = mock.report || {}
  const portrait = mock.portrait || {}
  return {
    id: mock.id,
    full_name: mock.full_name,
    amount: mock.amount,
    purpose: mock.purpose,
    status: STATUS_TO_APPLICATION_STATUS[mock.status] || APPLICATION_STATUS.IN_QUEUE,
    score: mock.score,
    created_at: mock.created_at,
    downloads: Array.isArray(report.downloads) ? report.downloads : [],
    decided_by_employee: mock.decided_by
      ? {
          full_name: mock.decided_by.full_name,
          login: mock.decided_by.login,
        }
      : null,
    decided_at: mock.decided_by ? mock.decided_by.decided_at : null,
    score_result: {
      score: mock.score,
      positive_signals: mock.positive_signals || [],
      risk_factors: mock.risk_factors || [],
      stability_score: portrait.stability != null ? portrait.stability : 0,
      financial_literacy_score:
        portrait.financial_literacy != null ? portrait.financial_literacy : 0,
      responsibility_score: portrait.responsibility != null ? portrait.responsibility : 0,
      report_content: buildReportContent(mock),
      report_updated_at: report.updated_at || null,
    },
  }
}