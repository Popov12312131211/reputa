import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Clock, Check, X, Filter } from 'lucide-react'
import { getJSON } from '../api'
import { APPLICATION_STATUS, STATUS_GROUP } from '../constants/application'
import ScoreGauge from './ScoreGauge'
import './UserMy.css'

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

// Бейдж статуса: та же иконография/цвета, что в таблице /user/my (APP-004).
function StatusBadge({ status, title }) {
  const Icon = STATUS_ICON[status] || Clock
  return (
    <span
      className={`usermy-status usermy-status--${STATUS_GROUP[status] || 'pending'}`}
      title={title}
    >
      <Icon size={16} strokeWidth={1.5} />
    </span>
  )
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
  const [searchParams, setSearchParams] = useSearchParams()
  const [applications, setApplications] = useState(null)
  const [filter, setFilter] = useState('all')
  const [filterOpen, setFilterOpen] = useState(false)
  const [sort, setSort] = useState({ key: 'date', dir: 'desc' })
  const [detail, setDetail] = useState(null)
  const [loadError, setLoadError] = useState(false)

  const menuId = searchParams.get('menu')

  function handleSort(key) {
    setSort((prev) =>
      prev.key === key ? { key, dir: prev.dir === 'desc' ? 'asc' : 'desc' } : { key, dir: 'asc' }
    )
  }

  function openDetail(app) {
    setSearchParams({ menu: String(app.id) })
  }

  function closeDetail() {
    setSearchParams({})
  }

  useEffect(() => {
    let cancelled = false
    getJSON('/api/user/applications').then((res) => {
      if (cancelled) return
      if (res.ok && Array.isArray(res.data)) {
        setApplications(res.data)
        setLoadError(false)
      } else {
        setApplications(null)
        setLoadError(true)
      }
    })
    return () => {
      cancelled = true
    }
  }, [])

  // APP-005: детальная карточка открывается по ?menu={id}. Данные берём с
  // бэкенда (эндпоинт проверяет принадлежность заявки текущему пользователю);
  // отдельная строка из списка не подставляется — карточка целиком живёт
  // на данных GET /user/applications/{application_id}.
  useEffect(() => {
    if (menuId == null) {
      setDetail(null)
      return
    }
    let cancelled = false
    setDetail({ status: 'loading' })
    getJSON(`/api/user/applications/${menuId}`).then((res) => {
      if (cancelled) return
      if (res.ok) {
        setDetail({ status: 'ready', data: res.data })
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
    if (menuId == null) return
    const onKey = (e) => {
      if (e.key === 'Escape') closeDetail()
    }
    document.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [menuId])

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
        va = new Date(a.created_at).getTime()
        vb = new Date(b.created_at).getTime()
      }
      const diff = va - vb
      return sort.dir === 'desc' ? diff * -1 : diff
    })
    return sorted
  }, [applications, filter, sort])

  const detailApp = detail && detail.status === 'ready' ? detail.data : null

  return (
    <div className="usermy-page">
      <div className="usermy-page__inner">
        <h1 className="usermy-page__title">{t('userMy.title')}</h1>

        <div className="usermy-card">
          {loadError ? (
            <div className="usermy-empty">
              <p className="usermy-empty__text">{t('userMy.loadError')}</p>
            </div>
          ) : applications && applications.length === 0 ? (
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

                {filtered.map((app) => (
                  <div
                    className="usermy-table__row"
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
                    <div className="usermy-table__cell usermy-table__cell--id" role="cell">
                      {app.id}
                    </div>
                    <div className="usermy-table__cell" role="cell">
                      <StatusBadge
                        status={app.status}
                        title={t(
                          `userMy.filter${STATUS_GROUP[app.status] ? STATUS_GROUP[app.status].charAt(0).toUpperCase() + STATUS_GROUP[app.status].slice(1) : 'Pending'}`
                        )}
                      />
                    </div>
                    <div className="usermy-table__cell usermy-table__cell--amount" role="cell">
                      {formatAmount(app.amount)} ₽
                    </div>
                    <div className="usermy-table__cell usermy-table__cell--date" role="cell">
                      {formatDate(app.created_at)}
                    </div>
                    <div className="usermy-table__cell usermy-table__cell--score" role="cell">
                      {app.score != null ? app.score : '—'}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* APP-005: детальная карточка заявки — модальное окно поверх списка */}
      {menuId != null && (
        <div className="usermy-modal" onClick={closeDetail}>
          <div
            className="usermy-modal__dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="usermy-detail-title"
            onClick={(e) => e.stopPropagation()}
          >
            {detail && detail.status === 'loading' && (
              <div className="usermy-detail__message">{t('userMyDetail.loading')}</div>
            )}
            {detail && detail.status === 'error' && (
              <div className="usermy-detail__message">{t('userMyDetail.notFound')}</div>
            )}
            {detailApp && (
              <>
                <div className="usermy-detail__header">
                  <div className="usermy-detail__header-main">
                    <StatusBadge status={detailApp.status} />
                    <div className="usermy-detail__header-text" id="usermy-detail-title">
                      <div className="usermy-detail__id">{detailApp.id}</div>
                      <div className="usermy-detail__fio">{detailApp.full_name}</div>
                    </div>
                  </div>
                  <div className="usermy-detail__request">
                    <span className="usermy-detail__request-label">{t('userMyDetail.request')}:</span>
                    <span className="usermy-detail__request-amount">
                      {formatAmount(detailApp.amount)} ₽
                    </span>
                  </div>
                  <button
                    className="usermy-detail__close"
                    type="button"
                    aria-label={t('userMyDetail.close')}
                    onClick={closeDetail}
                  >
                    <X size={18} strokeWidth={1.5} />
                  </button>
                </div>

                <div className="usermy-detail__block">
                  <h2 className="usermy-detail__block-title">{t('userMyDetail.creditPurpose')}</h2>
                  <textarea
                    className="usermy-detail__purpose"
                    readOnly
                    value={detailApp.purpose}
                  />
                </div>

                <div className="usermy-detail__block">
                  <h2 className="usermy-detail__block-title">{t('userMyDetail.finalScore')}</h2>
                  <div className="usermy-detail__score">
                    <ScoreGauge value={detailApp.score} />
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}