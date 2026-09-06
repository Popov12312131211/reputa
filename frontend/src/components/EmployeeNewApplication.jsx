import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Clock, Check, X, Search, Hash } from 'lucide-react'
import { getJSON } from '../api'
import { APPLICATION_STATUS, STATUS_GROUP } from '../constants/application'
import ApplicationDetailModal from './ApplicationDetail'
import './EmployeeNewApplication.css'

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

// Бейдж статуса: та же иконография/цвета, что в таблице /user/my (APP-004).
function StatusBadge({ status, title }) {
  const Icon = STATUS_ICON[status] || Clock
  return (
    <span
      className={`empnewapp-status empnewapp-status--${STATUS_GROUP[status] || 'pending'}`}
      title={title}
    >
      <Icon size={16} strokeWidth={1.5} />
    </span>
  )
}

function SortButton({ label, dir, active, ariaLabel, onSort }) {
  return (
    <button
      className={`empnewapp-table__sort${active ? ' empnewapp-table__sort--active' : ''}`}
      type="button"
      aria-label={ariaLabel}
      onClick={onSort}
    >
      <span>{label}</span>
      {active && (
        <span className={`empnewapp-table__sort-arrow${dir === 'asc' ? ' empnewapp-table__sort-arrow--asc' : ''}`}>↓</span>
      )}
    </button>
  )
}

export default function EmployeeNewApplication() {
  const { t } = useTranslation()
  const [searchParams, setSearchParams] = useSearchParams()
  const [applications, setApplications] = useState(null)
  const [query, setQuery] = useState('')
  const [idQuery, setIdQuery] = useState('')
  const [sort, setSort] = useState({ key: 'date', dir: 'asc' })

  const menuId = searchParams.get('menu')

  useEffect(() => {
    let cancelled = false
    getJSON('/api/employee/applications').then((res) => {
      if (cancelled) return
      if (res.ok && Array.isArray(res.data)) {
        setApplications(res.data)
      } else {
        setApplications([])
      }
    })
    return () => {
      cancelled = true
    }
  }, [])

  function handleSort(key) {
    setSort((prev) =>
      prev.key === key ? { key, dir: prev.dir === 'desc' ? 'asc' : 'desc' } : { key, dir: 'asc' }
    )
  }

  // EMP-005: детальная карточка заявки открывается по ?menu={id} — общий
  // компонент ApplicationDetailModal, тот же, что в /employee/application.
  function openDetail(app) {
    setSearchParams({ menu: String(app.id) })
  }

  function closeDetail() {
    setSearchParams({})
  }

  // После решения заявки из карточки обновляем её статус в строке таблицы.
  function updateRow(applicationId, newStatus) {
    setApplications((prev) =>
      prev == null
        ? prev
        : prev.map((app) =>
            app.id === applicationId ? { ...app, status: newStatus } : app
          )
    )
  }

  // Страница показывает только заявки «на рассмотрении» (IN_QUEUE): решённые
  // (одобренные/отклонённые) сюда не попадают ни из реального ответа, ни из
  // мока. Дальше — поиск по ФИО + ID и сортировка (поиск по подстроке без
  // учёта регистра).
  const visible = useMemo(() => {
    let list = (applications || []).filter(
      (app) => app.status === APPLICATION_STATUS.IN_QUEUE
    )
    const q = query.trim().toLowerCase()
    if (q) {
      list = list.filter((app) => (app.full_name || '').toLowerCase().includes(q))
    }
    const qi = idQuery.trim().toLowerCase()
    if (qi) {
      list = list.filter((app) => String(app.id).toLowerCase().includes(qi))
    }
    const sorted = [...list].sort((a, b) => {
      let va
      let vb
      if (sort.key === 'amount') {
        va = Number(a.amount)
        vb = Number(b.amount)
      } else if (sort.key === 'score') {
        // null-оценка (заявка ещё без итоговой оценки) — всегда в конец,
        // независимо от направления сортировки.
        const fallback = sort.dir === 'desc' ? Number.NEGATIVE_INFINITY : Number.POSITIVE_INFINITY
        va = a.score != null ? a.score : fallback
        vb = b.score != null ? b.score : fallback
      } else {
        va = new Date(a.created_at).getTime()
        vb = new Date(b.created_at).getTime()
      }
      const diff = va - vb
      return sort.dir === 'desc' ? diff * -1 : diff
    })
    return sorted
  }, [applications, query, idQuery, sort])

  const hasQuery = query.trim().length > 0 || idQuery.trim().length > 0

  return (
    <div className="empnewapp-page">
      <div className="empnewapp-page__inner">
        <h1 className="empnewapp-page__title">{t('employeeNewApplication.title')}</h1>

        <div className="empnewapp-card">
          <div className="empnewapp-search">
            <div className="empnewapp-search__field">
              <span className="empnewapp-search__icon">
                <Search size={16} strokeWidth={1.5} />
              </span>
              <input
                className="empnewapp-search__input"
                type="search"
                placeholder={t('employeeNewApplication.searchPlaceholder')}
                aria-label={t('employeeNewApplication.search')}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
            <div className="empnewapp-search__field">
              <span className="empnewapp-search__icon">
                <Hash size={16} strokeWidth={1.5} />
              </span>
              <input
                className="empnewapp-search__input"
                type="search"
                placeholder={t('employeeNewApplication.idPlaceholder')}
                aria-label={t('employeeNewApplication.idSearch')}
                value={idQuery}
                onChange={(e) => setIdQuery(e.target.value)}
              />
            </div>
            {hasQuery && (
              <button
                className="empnewapp-search__clear"
                type="button"
                aria-label={t('employeeNewApplication.clearSearch')}
                onClick={() => {
                  setQuery('')
                  setIdQuery('')
                }}
              >
                <X size={14} strokeWidth={1.5} />
              </button>
            )}
          </div>

          {applications != null && hasQuery && visible.length === 0 ? (
            <div className="empnewapp-empty">
              <p className="empnewapp-empty__text">{t('employeeNewApplication.emptySearch')}</p>
            </div>
          ) : applications != null && visible.length === 0 ? (
            <div className="empnewapp-empty">
              <p className="empnewapp-empty__text">{t('employeeNewApplication.empty')}</p>
            </div>
          ) : applications != null && (
            <div className="empnewapp-table" role="table" aria-label={t('employeeNewApplication.title')}>
              <div className="empnewapp-table__head" role="row">
                <div className="empnewapp-table__cell empnewapp-table__cell--head" role="columnheader">
                  {t('employeeNewApplication.colId')}
                </div>
                <div className="empnewapp-table__cell empnewapp-table__cell--head" role="columnheader">
                  {t('employeeNewApplication.colStatus')}
                </div>
                <div className="empnewapp-table__cell empnewapp-table__cell--head" role="columnheader">
                  {t('employeeNewApplication.colFio')}
                </div>
                <div className="empnewapp-table__cell empnewapp-table__cell--head" role="columnheader">
                  <SortButton
                    label={t('employeeNewApplication.colAmount')}
                    dir={sort.dir}
                    active={sort.key === 'amount'}
                    ariaLabel={t('employeeNewApplication.sortToggle', {
                      column: t('employeeNewApplication.colAmount'),
                      dir: sort.dir === 'asc' ? t('employeeNewApplication.sortAsc') : t('employeeNewApplication.sortDesc'),
                    })}
                    onSort={() => handleSort('amount')}
                  />
                </div>
                <div className="empnewapp-table__cell empnewapp-table__cell--head" role="columnheader">
                  <SortButton
                    label={t('employeeNewApplication.colDate')}
                    dir={sort.dir}
                    active={sort.key === 'date'}
                    ariaLabel={t('employeeNewApplication.sortToggle', {
                      column: t('employeeNewApplication.colDate'),
                      dir: sort.dir === 'asc' ? t('employeeNewApplication.sortAsc') : t('employeeNewApplication.sortDesc'),
                    })}
                    onSort={() => handleSort('date')}
                  />
                </div>
                <div className="empnewapp-table__cell empnewapp-table__cell--head" role="columnheader">
                  <SortButton
                    label={t('employeeNewApplication.colScore')}
                    dir={sort.dir}
                    active={sort.key === 'score'}
                    ariaLabel={t('employeeNewApplication.sortToggle', {
                      column: t('employeeNewApplication.colScore'),
                      dir: sort.dir === 'asc' ? t('employeeNewApplication.sortAsc') : t('employeeNewApplication.sortDesc'),
                    })}
                    onSort={() => handleSort('score')}
                  />
                </div>
              </div>

              {visible.map((app) => (
                <div
                  className="empnewapp-table__row"
                  role="row"
                  key={app.id}
                  tabIndex={0}
                  aria-label={String(app.id)}
                  onClick={() => openDetail(app)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      openDetail(app)
                    }
                  }}
                >
                  <div className="empnewapp-table__cell empnewapp-table__cell--id" role="cell">
                    {app.id}
                  </div>
                  <div className="empnewapp-table__cell" role="cell">
                    <StatusBadge
                      status={app.status}
                      title={t(
                        `employeeNewApplication.filter${STATUS_GROUP[app.status] ? STATUS_GROUP[app.status].charAt(0).toUpperCase() + STATUS_GROUP[app.status].slice(1) : 'Pending'}`
                      )}
                    />
                  </div>
                  <div className="empnewapp-table__cell empnewapp-table__cell--fio" role="cell">
                    {app.full_name}
                  </div>
                  <div className="empnewapp-table__cell empnewapp-table__cell--amount" role="cell">
                    {formatAmount(app.amount)} ₽
                  </div>
                  <div className="empnewapp-table__cell empnewapp-table__cell--date" role="cell">
                    {formatDate(app.created_at)}
                  </div>
                  <div className="empnewapp-table__cell empnewapp-table__cell--score" role="cell">
                    {app.score != null ? app.score : '—'}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* EMP-005: детальная карточка заявки (общий компонент) по ?menu={id}. */}
      {menuId != null && (
        <ApplicationDetailModal
          menuId={menuId}
          onClose={closeDetail}
          onDecided={updateRow}
        />
      )}
    </div>
  )
}