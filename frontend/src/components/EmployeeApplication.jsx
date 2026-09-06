import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Clock, Check, X, Search, Filter, Hash } from 'lucide-react'
import { getJSON } from '../api'
import { APPLICATION_STATUS, STATUS_GROUP } from '../constants/application'
import { mockApplications, toEmployeeApplication } from '../mocks/employeeApplications'
import ApplicationDetailModal from './ApplicationDetail'
import './EmployeeApplication.css'

const STATUS_ICON = {
  [APPLICATION_STATUS.IN_QUEUE]: Clock,
  [APPLICATION_STATUS.AUTO_APPROVED]: Check,
  [APPLICATION_STATUS.AUTO_REJECTED]: X,
  [APPLICATION_STATUS.EMPLOYEE_APPROVED]: Check,
  [APPLICATION_STATUS.EMPLOYEE_REJECTED]: X,
}

const FILTER_OPTIONS = ['all', 'pending', 'approved', 'rejected']

const PENDING_STATUSES = new Set([APPLICATION_STATUS.IN_QUEUE])
const APPROVED_STATUSES = new Set([
  APPLICATION_STATUS.AUTO_APPROVED,
  APPLICATION_STATUS.EMPLOYEE_APPROVED,
])
const REJECTED_STATUSES = new Set([
  APPLICATION_STATUS.AUTO_REJECTED,
  APPLICATION_STATUS.EMPLOYEE_REJECTED,
])

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

function StatusBadge({ status, title }) {
  const Icon = STATUS_ICON[status] || Clock
  return (
    <span
      className={`empapp-status empapp-status--${STATUS_GROUP[status] || 'pending'}`}
      title={title}
    >
      <Icon size={16} strokeWidth={1.5} />
    </span>
  )
}

function SortButton({ label, dir, active, ariaLabel, onSort }) {
  return (
    <button
      className={`empapp-table__sort${active ? ' empapp-table__sort--active' : ''}`}
      type="button"
      aria-label={ariaLabel}
      onClick={onSort}
    >
      <span>{label}</span>
      {active && (
        <span className={`empapp-table__sort-arrow${dir === 'asc' ? ' empapp-table__sort-arrow--asc' : ''}`}>↓</span>
      )}
    </button>
  )
}

export default function EmployeeApplication() {
  const { t } = useTranslation()
  const [searchParams, setSearchParams] = useSearchParams()
  const [applications, setApplications] = useState(null)
  const [query, setQuery] = useState('')
  const [idQuery, setIdQuery] = useState('')
  const [filter, setFilter] = useState('all')
  const [filterOpen, setFilterOpen] = useState(false)
  const [sort, setSort] = useState({ key: 'date', dir: 'desc' })

  const menuId = searchParams.get('menu')

  useEffect(() => {
    let cancelled = false
    getJSON('/api/employee/applications').then((res) => {
      if (cancelled) return
      if (res.ok && Array.isArray(res.data)) {
        setApplications(res.data)
      } else {
        setApplications(mockApplications.map(toEmployeeApplication))
      }
    })
    return () => {
      cancelled = true
    }
  }, [])

  function openDetail(app) {
    setSearchParams({ menu: String(app.id) })
  }

  function closeDetail() {
    setSearchParams({})
  }

  function handleSort(key) {
    setSort((prev) =>
      prev.key === key ? { key, dir: prev.dir === 'desc' ? 'asc' : 'desc' } : { key, dir: 'asc' }
    )
  }

  // EMP-005: после решения заявки из карточки обновляем её статус в списке,
  // чтобы таблица не показывала устаревшее состояние.
  function updateRow(applicationId, newStatus) {
    setApplications((prev) =>
      prev == null
        ? prev
        : prev.map((app) =>
            app.id === applicationId ? { ...app, status: newStatus } : app
          )
    )
  }

  const visible = useMemo(() => {
    let list = applications || []
    if (filter !== 'all') {
      list = list.filter((app) => {
        if (filter === 'pending') return PENDING_STATUSES.has(app.status)
        if (filter === 'approved') return APPROVED_STATUSES.has(app.status)
        if (filter === 'rejected') return REJECTED_STATUSES.has(app.status)
        return false
      })
    }
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
  }, [applications, query, idQuery, filter, sort])

  const hasQuery = query.trim().length > 0 || idQuery.trim().length > 0

  return (
    <div className="empapp-page">
      <div className="empapp-page__inner">
        <h1 className="empapp-page__title">{t('employeeApplication.title')}</h1>

        <div className="empapp-card">
          {applications != null && applications.length === 0 ? (
            <div className="empapp-empty">
              <p className="empapp-empty__text">{t('employeeApplication.empty')}</p>
            </div>
          ) : (
            <>
              <div className="empapp-search">
                <div className="empapp-search__field">
                  <span className="empapp-search__icon">
                    <Search size={16} strokeWidth={1.5} />
                  </span>
                  <input
                    className="empapp-search__input"
                    type="search"
                    placeholder={t('employeeApplication.searchPlaceholder')}
                    aria-label={t('employeeApplication.search')}
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                  />
                </div>
                <div className="empapp-search__field">
                  <span className="empapp-search__icon">
                    <Hash size={16} strokeWidth={1.5} />
                  </span>
                  <input
                    className="empapp-search__input"
                    type="search"
                    placeholder={t('employeeApplication.idPlaceholder')}
                    aria-label={t('employeeApplication.idSearch')}
                    value={idQuery}
                    onChange={(e) => setIdQuery(e.target.value)}
                  />
                </div>
                {hasQuery && (
                  <button
                    className="empapp-search__clear"
                    type="button"
                    aria-label={t('employeeApplication.clearSearch')}
                    onClick={() => {
                      setQuery('')
                      setIdQuery('')
                    }}
                  >
                    <X size={14} strokeWidth={1.5} />
                  </button>
                )}
              </div>

              {hasQuery && visible.length === 0 ? (
                <div className="empapp-empty">
                  <p className="empapp-empty__text">{t('employeeApplication.emptySearch')}</p>
                </div>
              ) : (
                <div className="empapp-table" role="table" aria-label={t('employeeApplication.title')}>
                  <div className="empapp-table__head" role="row">
                    <div className="empapp-table__cell empapp-table__cell--head" role="columnheader">
                      {t('employeeApplication.colId')}
                    </div>
                    <div className="empapp-table__cell empapp-table__cell--head" role="columnheader">
                      <span>{t('employeeApplication.colStatus')}</span>
                      <div className="empapp-filter">
                        <button
                          className="empapp-filter__button"
                          type="button"
                          aria-label={t('employeeApplication.filterTitle')}
                          aria-expanded={filterOpen}
                          onClick={() => setFilterOpen((v) => !v)}
                        >
                          <Filter size={14} strokeWidth={1.5} />
                        </button>
                        {filterOpen && (
                          <div className="empapp-filter__menu">
                            {FILTER_OPTIONS.map((opt) => (
                              <button
                                key={opt}
                                className={`empapp-filter__option${filter === opt ? ' empapp-filter__option--active' : ''}`}
                                type="button"
                                onClick={() => {
                                  setFilter(opt)
                                  setFilterOpen(false)
                                }}
                              >
                                {t(`employeeApplication.filter${opt.charAt(0).toUpperCase()}${opt.slice(1)}`)}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="empapp-table__cell empapp-table__cell--head" role="columnheader">
                      {t('employeeApplication.colFio')}
                    </div>
                    <div className="empapp-table__cell empapp-table__cell--head" role="columnheader">
                      <SortButton
                        label={t('employeeApplication.colAmount')}
                        dir={sort.dir}
                        active={sort.key === 'amount'}
                        ariaLabel={t('employeeApplication.sortToggle', {
                          column: t('employeeApplication.colAmount'),
                          dir: sort.dir === 'asc' ? t('employeeApplication.sortAsc') : t('employeeApplication.sortDesc'),
                        })}
                        onSort={() => handleSort('amount')}
                      />
                    </div>
                    <div className="empapp-table__cell empapp-table__cell--head" role="columnheader">
                      <SortButton
                        label={t('employeeApplication.colDate')}
                        dir={sort.dir}
                        active={sort.key === 'date'}
                        ariaLabel={t('employeeApplication.sortToggle', {
                          column: t('employeeApplication.colDate'),
                          dir: sort.dir === 'asc' ? t('employeeApplication.sortAsc') : t('employeeApplication.sortDesc'),
                        })}
                        onSort={() => handleSort('date')}
                      />
                    </div>
                    <div className="empapp-table__cell empapp-table__cell--head" role="columnheader">
                      <SortButton
                        label={t('employeeApplication.colScore')}
                        dir={sort.dir}
                        active={sort.key === 'score'}
                        ariaLabel={t('employeeApplication.sortToggle', {
                          column: t('employeeApplication.colScore'),
                          dir: sort.dir === 'asc' ? t('employeeApplication.sortAsc') : t('employeeApplication.sortDesc'),
                        })}
                        onSort={() => handleSort('score')}
                      />
                    </div>
                  </div>

                  {visible.map((app) => (
                    <div
                      className="empapp-table__row"
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
                      <div className="empapp-table__cell empapp-table__cell--id" role="cell">
                        {app.id}
                      </div>
                      <div className="empapp-table__cell" role="cell">
                        <StatusBadge
                          status={app.status}
                          title={t(
                            `employeeApplication.filter${STATUS_GROUP[app.status] ? STATUS_GROUP[app.status].charAt(0).toUpperCase() + STATUS_GROUP[app.status].slice(1) : 'Pending'}`
                          )}
                        />
                      </div>
                      <div className="empapp-table__cell empapp-table__cell--fio" role="cell">
                        {app.full_name}
                      </div>
                      <div className="empapp-table__cell empapp-table__cell--amount" role="cell">
                        {formatAmount(app.amount)} ₽
                      </div>
                      <div className="empapp-table__cell empapp-table__cell--date" role="cell">
                        {formatDate(app.created_at)}
                      </div>
                      <div className="empapp-table__cell empapp-table__cell--score" role="cell">
                        {app.score != null ? app.score : '—'}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* EMP-005: детальная карточка заявки сотрудника — общий компонент
          (тот же, что в /employee/newApplication), открывается по ?menu={id}. */}
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