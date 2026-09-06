import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AlertTriangle, Check, Clock, Download, X } from 'lucide-react'
import { getJSON, postJSON } from '../api'
import { APPLICATION_STATUS, STATUS_GROUP } from '../constants/application'
import ScoreGauge from './ScoreGauge'
import './ApplicationDetail.css'

const STATUS_ICON = {
  [APPLICATION_STATUS.IN_QUEUE]: Clock,
  [APPLICATION_STATUS.AUTO_APPROVED]: Check,
  [APPLICATION_STATUS.AUTO_REJECTED]: X,
  [APPLICATION_STATUS.EMPLOYEE_APPROVED]: Check,
  [APPLICATION_STATUS.EMPLOYEE_REJECTED]: X,
}

function formatAmount(value) {
  return new Intl.NumberFormat('ru-RU').format(value)
}

function formatDate(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(date)
}

function formatDateTime(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

// EMP-005: единая детальная карточка заявки сотрудника. Переиспользуется
// на /employee/application и /employee/newApplication (открывается по
// ?menu={id}) — обе страницы подключают один компонент, данные и действия
// по заявке живут здесь, а не дублируются в списках.
function StatusBadge({ status, title }) {
  const Icon = STATUS_ICON[status] || Clock
  return (
    <span
      className={`appdetail-status appdetail-status--${STATUS_GROUP[status] || 'pending'}`}
      title={title}
    >
      <Icon size={16} strokeWidth={1.5} />
    </span>
  )
}

// EMP-005: метрика психологического портрета 0–10 с линейной шкалой.
function PortraitMetric({ label, value }) {
  const { t } = useTranslation()
  const pct = Math.max(0, Math.min(10, Number(value) || 0)) * 10
  return (
    <div className="appdetail-metric">
      <span className="appdetail-metric__label">{label}</span>
      <div className="appdetail-metric__track">
        <div className="appdetail-metric__fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="appdetail-metric__value">
        {t('employeeApplicationDetail.metricValue', { value: Number(value) || 0 })}
      </span>
    </div>
  )
}

export default function ApplicationDetailModal({ menuId, onClose, onDecided }) {
  const { t } = useTranslation()
  const [detail, setDetail] = useState(null)
  const [deciding, setDeciding] = useState(false)
  const [decisionError, setDecisionError] = useState(null)
  const [downloads, setDownloads] = useState([])

  const app = detail && detail.status === 'ready' ? detail.data : null
  const scoreResult = app && app.score_result ? app.score_result : null

  // Карточка целиком живёт на ответе GET /employee/applications/{id} —
  // отдельная строка из списка не подставляется. При недоступности эндпоинта
  // статус карточки — ошибка.
  useEffect(() => {
    if (menuId == null) {
      setDetail(null)
      setDownloads([])
      return
    }
    let cancelled = false
    setDetail({ status: 'loading' })
    setDownloads([])
    getJSON(`/api/employee/applications/${menuId}`).then((res) => {
      if (cancelled) return
      if (res.ok) {
        setDetail({ status: 'ready', data: res.data })
        setDownloads(Array.isArray(res.data.downloads) ? res.data.downloads : [])
        return
      }
      setDetail({ status: 'error' })
    })
    return () => {
      cancelled = true
    }
  }, [menuId])

  // Закрытие по Escape и блокировка прокрутки страницы под модальным окном.
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
    }
  }, [onClose])

  function statusLabel(status) {
    const group = STATUS_GROUP[status]
    if (group === 'approved') return t('employeeApplication.filterApproved')
    if (group === 'rejected') return t('employeeApplication.filterRejected')
    return t('employeeApplication.filterPending')
  }

  function updateApplication(applicationId, newStatus) {
    if (onDecided) onDecided(applicationId, newStatus)
  }

  async function handleDecision(decision) {
    if (!app || deciding) return
    setDeciding(true)
    setDecisionError(null)
    const res = await postJSON(`/api/applications/${app.id}/decision`, { decision })
    if (res.ok) {
      const newStatus =
        decision === 'approve'
          ? APPLICATION_STATUS.EMPLOYEE_APPROVED
          : APPLICATION_STATUS.EMPLOYEE_REJECTED
      updateApplication(app.id, newStatus)
      // Перезапрашиваем карточку: после решения бэкенд возвращает ФИО и логин
      // сотрудника, принявшего решение (decided_by_employee).
      const updated = await getJSON(`/api/employee/applications/${menuId}`)
      if (updated.ok) {
        setDetail({ status: 'ready', data: updated.data })
      } else {
        setDetail({ status: 'ready', data: { ...app, status: newStatus } })
      }
    } else {
      setDecisionError(res.error || t('employeeApplicationDetail.decideError'))
    }
    setDeciding(false)
  }

  // EMP-005: история скачиваний приходит с бэкенда (GET /employee/applications/{id}),
  // новые записи добавляются в момент реальной выгрузки файла.
  function generateDownloadId() {
    return `ID${Math.floor(100000000 + Math.random() * 900000000)}`
  }

  function handleDownload() {
    if (!app || !scoreResult || !scoreResult.report_content) return
    const blob = new Blob([scoreResult.report_content], {
      type: 'text/plain;charset=utf-8',
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `report-${app.id}.txt`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    setDownloads((prev) => [{ date: new Date(), id: generateDownloadId() }, ...prev])
  }

  return (
    <div className="appdetail-modal" onClick={onClose}>
      <div
        className="appdetail-modal__dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="appdetail-title"
        onClick={(e) => e.stopPropagation()}
      >
        {detail && detail.status === 'loading' && (
          <div className="appdetail-message">{t('employeeApplicationDetail.loading')}</div>
        )}
        {detail && detail.status === 'error' && (
          <div className="appdetail-message">{t('employeeApplicationDetail.notFound')}</div>
        )}
        {app && (
          <>
            <div className="appdetail-header">
              <div className="appdetail-header__main">
                <StatusBadge status={app.status} title={statusLabel(app.status)} />
                <div className="appdetail-header__text" id="appdetail-title">
                  <div className="appdetail-header__id">{app.id}</div>
                  <div className="appdetail-header__fio">{app.full_name}</div>
                </div>
              </div>
              <div className="appdetail-header__request">
                <span className="appdetail-header__request-label">
                  {t('employeeApplicationDetail.request')}:
                </span>
                <span className="appdetail-header__request-amount">
                  {formatAmount(app.amount)} ₽
                </span>
              </div>
              <button
                className="appdetail-header__close"
                type="button"
                aria-label={t('employeeApplicationDetail.close')}
                onClick={onClose}
              >
                <X size={18} strokeWidth={1.5} />
              </button>
            </div>

            <div className="appdetail-section">
              <h2 className="appdetail-section__title">
                {t('employeeApplicationDetail.creditPurpose')}
              </h2>
              <div className="appdetail-purpose">{app.purpose}</div>
            </div>

            <div className="appdetail-section">
              <h2 className="appdetail-section__title">
                {t('employeeApplicationDetail.recommendationsTitle')}
              </h2>
              {scoreResult ? (
                <div className="appdetail-rec">
                  <div className="appdetail-rec__group">
                    <h3 className="appdetail-rec__title appdetail-rec__title--positive">
                      {t('employeeApplicationDetail.positiveSignals')}
                    </h3>
                    {scoreResult.positive_signals.length > 0 ? (
                      <ul className="appdetail-rec__list">
                        {scoreResult.positive_signals.map((signal, i) => (
                          <li
                            key={i}
                            className="appdetail-rec__badge appdetail-rec__badge--positive"
                          >
                            <Check size={14} strokeWidth={2} />
                            <span>{signal}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="appdetail-rec__empty">
                        {t('employeeApplicationDetail.noSignals')}
                      </p>
                    )}
                  </div>
                  <div className="appdetail-rec__group">
                    <h3 className="appdetail-rec__title appdetail-rec__title--risk">
                      {t('employeeApplicationDetail.riskFactors')}
                    </h3>
                    {scoreResult.risk_factors.length > 0 ? (
                      <ul className="appdetail-rec__list">
                        {scoreResult.risk_factors.map((factor, i) => (
                          <li key={i} className="appdetail-rec__badge appdetail-rec__badge--risk">
                            <AlertTriangle size={14} strokeWidth={2} />
                            <span>{factor}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="appdetail-rec__empty">
                        {t('employeeApplicationDetail.noRiskFactors')}
                      </p>
                    )}
                  </div>
                </div>
              ) : (
                <p className="appdetail-empty">{t('employeeApplicationDetail.noAnalytics')}</p>
              )}
            </div>

            {/* EMP-005: портрет и отчёт — две колонки бок о бок выше итоговой оценки. */}
            <div className="appdetail-columns">
              <div className="appdetail-column">
                <div className="appdetail-section">
                  <h2 className="appdetail-section__title">
                    {t('employeeApplicationDetail.portraitTitle')}
                  </h2>
                  {scoreResult ? (
                    <div className="appdetail-portrait">
                      <PortraitMetric
                        label={t('employeeApplicationDetail.stability')}
                        value={scoreResult.stability_score}
                      />
                      <PortraitMetric
                        label={t('employeeApplicationDetail.financialLiteracy')}
                        value={scoreResult.financial_literacy_score}
                      />
                      <PortraitMetric
                        label={t('employeeApplicationDetail.responsibility')}
                        value={scoreResult.responsibility_score}
                      />
                    </div>
                  ) : (
                    <p className="appdetail-empty">{t('employeeApplicationDetail.noAnalytics')}</p>
                  )}
                </div>
              </div>
              <div className="appdetail-column">
                <div className="appdetail-section">
                  <h2 className="appdetail-section__title">
                    {t('employeeApplicationDetail.reportTitle')}
                  </h2>
                  {scoreResult ? (
                    <div className="appdetail-report">
                      <button
                        className="appdetail-report__download"
                        type="button"
                        onClick={handleDownload}
                      >
                        <Download size={16} strokeWidth={1.5} />
                        {t('employeeApplicationDetail.downloadReport')}
                      </button>
                      {scoreResult.report_updated_at && (
                        <span className="appdetail-report__date">
                          {t('employeeApplicationDetail.reportUpdatedAt')}:{' '}
                          {formatDate(scoreResult.report_updated_at)}
                        </span>
                      )}
                      <div className="appdetail-history">
                        <h3 className="appdetail-history__title">
                          {t('employeeApplicationDetail.downloadHistory')}
                        </h3>
                        {downloads.length > 0 ? (
                          <ul className="appdetail-history__list">
                            {downloads.map((entry, i) => (
                              <li key={i} className="appdetail-history__item">
                                – {formatDate(entry.date)} {entry.id}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p className="appdetail-history__empty">
                            {t('employeeApplicationDetail.downloadHistoryEmpty')}
                          </p>
                        )}
                      </div>
                    </div>
                  ) : (
                    <p className="appdetail-empty">{t('employeeApplicationDetail.noAnalytics')}</p>
                  )}
                </div>
              </div>
            </div>

            <div className="appdetail-section">
              <h2 className="appdetail-section__title appdetail-section__title--center">
                {t('employeeApplicationDetail.finalScore')}
              </h2>
              <div className="appdetail-score">
                <ScoreGauge value={app.score} />
              </div>
            </div>

            {app.status === APPLICATION_STATUS.IN_QUEUE ? (
              <div className="appdetail-actions">
                <button
                  className="appdetail-button appdetail-button--reject"
                  type="button"
                  disabled={deciding}
                  onClick={() => handleDecision('reject')}
                >
                  {t('employeeApplicationDetail.reject')}
                </button>
                <button
                  className="appdetail-button appdetail-button--approve"
                  type="button"
                  disabled={deciding}
                  onClick={() => handleDecision('approve')}
                >
                  {t('employeeApplicationDetail.approve')}
                </button>
              </div>
            ) : (
              <div className="appdetail-decided">
                <div className="appdetail-decided__status">
                  {t('employeeApplicationDetail.decided')}: {statusLabel(app.status)}
                </div>
                {app.decided_by_employee && (
                  <div className="appdetail-decided__employee">
                    {t('employeeApplicationDetail.decidedBy', {
                      fullName: app.decided_by_employee.full_name,
                      login: app.decided_by_employee.login,
                    })}
                  </div>
                )}
                {app.decided_at && (
                  <div className="appdetail-decided__date">
                    {t('employeeApplicationDetail.decidedAt', {
                      date: formatDateTime(app.decided_at),
                    })}
                  </div>
                )}
              </div>
            )}
            {decisionError && <p className="appdetail-error">{decisionError}</p>}
          </>
        )}
      </div>
    </div>
  )
}