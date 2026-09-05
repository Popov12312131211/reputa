import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Clock, Check, X, Filter } from 'lucide-react'
import { getJSON } from '../api'
import { APPLICATION_STATUS, STATUS_GROUP } from '../constants/application'
import './UserMy.css'

// Заглушка: бэкенд-эндпоинт заявок пользователя (APP-002+) ещё не реализован.
// Используем мок с имитацией задержки сети, чтобы не ломать вёрстку.
// TODO: заменить на реальный GET /api/applications/my (или /api/user/applications) после реализации APP-002.
const MOCK_APPLICATIONS = [
  { id: '123DE456', amount: 25000, score: 72, status: APPLICATION_STATUS.AUTO_APPROVED, createdAt: '2026-09-01T10:15:00.000Z' },
  { id: '123DE457', amount: 150000, score: 34, status: APPLICATION_STATUS.EMPLOYEE_REJECTED, createdAt: '2026-08-28T14:40:00.000Z' },
  { id: '123DE458', amount: 5000, score: null, status: APPLICATION_STATUS.IN_QUEUE, createdAt: '2026-09-04T09:05:00.000Z' },
  { id: '123DE459', amount: 120000, score: 88, status: APPLICATION_STATUS.EMPLOYEE_APPROVED, createdAt: '2026-08-30T18:22:00.000Z' },
]

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

function SortButton({ label, dir, active, ariaLabel, onSort }) {
  return (
    <button
      className={`usermy-table__sort${active ? ' usermy-table__sort--active' : ''}`}
      type="button"
      aria-label={ariaLabel}
      onClick={onSort}
    >
      <span>{label}</span>
      {active && (
        <span className={`usermy-table__sort-arrow${dir === 'asc' ? ' usermy-table__sort-arrow--asc' : ''}`}>↓</span>
      )}
    </button>
  )
}

export default function UserMy() {
  const { t } = useTranslation()
  const [applications, setApplications] = useState(null)
  const [filter, setFilter] = useState('all')
  const [filterOpen, setFilterOpen] = useState(false)
  const [sort, setSort] = useState({ key: 'date', dir: 'desc' })

  function handleSort(key) {
    setSort((prev) =>
      prev.key === key ? { key, dir: prev.dir === 'desc' ? 'asc' : 'desc' } : { key, dir: 'asc' }
    )
  }

  useEffect(() => {
    let cancelled = false
    getJSON('/api/user/applications').then((res) => {
      if (cancelled) return
      // Заглушка до реализации бэкенда: показываем мок.
      setApplications(res.ok && Array.isArray(res.data) ? res.data : MOCK_APPLICATIONS)
    })
    return () => {
      cancelled = true
    }
  }, [])

  const filtered = useMemo(() => {
    let list = applications || []
    if (filter !== 'all') {
      list = list.filter((app) => {
        if (filter === 'pending') return PENDING_STATUSES.has(app.status)
        if (filter === 'approved') return APPROVED_STATUSES.has(app.status)
        if (filter === 'rejected') return REJECTED_STATUSES.has(app.status)
        return false
      })
    }
    const sorted = [...list].sort((a, b) => {
      let va
      let vb
      if (sort.key === 'amount') {
        va = Number(a.amount)
        vb = Number(b.amount)
      } else if (sort.key === 'score') {
        // null-оценка (заявка ещё в обработке) — всегда в конец, независимо от направления
        const fallback = sort.dir === 'desc' ? Number.NEGATIVE_INFINITY : Number.POSITIVE_INFINITY
        va = a.score != null ? a.score : fallback
        vb = b.score != null ? b.score : fallback
      } else {
        va = new Date(a.createdAt).getTime()
        vb = new Date(b.createdAt).getTime()
      }
      const diff = va - vb
      return sort.dir === 'desc' ? diff * -1 : diff
    })
    return sorted
  }, [applications, filter, sort])

  return (
    <div className="usermy-page">
      <div className="usermy-page__inner">
        <h1 className="usermy-page__title">{t('userMy.title')}</h1>

        <div className="usermy-card">
          {applications && applications.length === 0 ? (
            <div className="usermy-empty">
              <p className="usermy-empty__text">{t('userMy.empty')}</p>
              <Link className="usermy-empty__link" to="/user/new">
                {t('userMy.emptyLink')}
              </Link>
            </div>
          ) : (
            <>
              <div className="usermy-table" role="table" aria-label={t('userMy.title')}>
                <div className="usermy-table__head" role="row">
                  <div className="usermy-table__cell usermy-table__cell--head" role="columnheader">
                    {t('userMy.colId')}
                  </div>
                  <div className="usermy-table__cell usermy-table__cell--head" role="columnheader">
                    <span>{t('userMy.colStatus')}</span>
                    <div className="usermy-filter">
                      <button
                        className="usermy-filter__button"
                        type="button"
                        aria-label={t('userMy.filterTitle')}
                        aria-expanded={filterOpen}
                        onClick={() => setFilterOpen((v) => !v)}
                      >
                        <Filter size={14} strokeWidth={1.5} />
                      </button>
                      {filterOpen && (
                        <div className="usermy-filter__menu">
                          {FILTER_OPTIONS.map((opt) => (
                            <button
                              key={opt}
                              className={`usermy-filter__option${filter === opt ? ' usermy-filter__option--active' : ''}`}
                              type="button"
                              onClick={() => {
                                setFilter(opt)
                                setFilterOpen(false)
                              }}
                            >
                              {t(`userMy.filter${opt.charAt(0).toUpperCase()}${opt.slice(1)}`)}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="usermy-table__cell usermy-table__cell--head" role="columnheader">
                    <SortButton
                      label={t('userMy.colAmount')}
                      dir={sort.dir}
                      active={sort.key === 'amount'}
                      ariaLabel={t('userMy.sortToggle', {
                        column: t('userMy.colAmount'),
                        dir: t(`userMy.sort${sort.key === 'amount' && sort.dir === 'asc' ? 'Desc' : 'Asc'}`),
                      })}
                      onSort={() => handleSort('amount')}
                    />
                  </div>
                  <div className="usermy-table__cell usermy-table__cell--head" role="columnheader">
                    <SortButton
                      label={t('userMy.colDate')}
                      dir={sort.dir}
                      active={sort.key === 'date'}
                      ariaLabel={t('userMy.sortToggle', {
                        column: t('userMy.colDate'),
                        dir: t(`userMy.sort${sort.key === 'date' && sort.dir === 'asc' ? 'Desc' : 'Asc'}`),
                      })}
                      onSort={() => handleSort('date')}
                    />
                  </div>
                  <div className="usermy-table__cell usermy-table__cell--head" role="columnheader">
                    <SortButton
                      label={t('userMy.colScore')}
                      dir={sort.dir}
                      active={sort.key === 'score'}
                      ariaLabel={t('userMy.sortToggle', {
                        column: t('userMy.colScore'),
                        dir: t(`userMy.sort${sort.key === 'score' && sort.dir === 'asc' ? 'Desc' : 'Asc'}`),
                      })}
                      onSort={() => handleSort('score')}
                    />
                  </div>
                </div>

                {filtered.map((app) => {
                  const Icon = STATUS_ICON[app.status] || Clock
                  return (
                    <div className="usermy-table__row" role="row" key={app.id}>
                      <div className="usermy-table__cell usermy-table__cell--id" role="cell">
                        {app.id}
                      </div>
                      <div className="usermy-table__cell" role="cell">
                        <span
                          className={`usermy-status usermy-status--${STATUS_GROUP[app.status] || 'pending'}`}
                          title={t(`userMy.filter${STATUS_GROUP[app.status] ? STATUS_GROUP[app.status].charAt(0).toUpperCase() + STATUS_GROUP[app.status].slice(1) : 'Pending'}`)}
                        >
                          <Icon size={16} strokeWidth={1.5} />
                        </span>
                      </div>
                      <div className="usermy-table__cell usermy-table__cell--amount" role="cell">
                        {formatAmount(app.amount)} ₽
                      </div>
                      <div className="usermy-table__cell usermy-table__cell--date" role="cell">
                        {formatDate(app.createdAt)}
                      </div>
                      <div className="usermy-table__cell usermy-table__cell--score" role="cell">
                        {app.score != null ? app.score : '—'}
                      </div>
                    </div>
                  )
                })}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
