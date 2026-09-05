import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { getJSON, putJSON } from '../api'
import { THRESHOLD } from '../constants/threshold'
import './EmployeeSettings.css'

// Пустое поле — не число: Number('') === 0 неверно трактовал бы очищенное
// поле как порог 0, поэтому пустую строку отображаем в NaN (невалидно).
function toThresholdNumber(value) {
  if (value.trim() === '') return NaN
  return Number(value)
}

export default function EmployeeSettings() {
  const { t } = useTranslation()

  // Значения порогов держим в строках полей ввода и синхронизируем с БД
  // через GET/PUT /api/employee/settings (EMP-002).
  const [reject, setReject] = useState('')
  const [approve, setApprove] = useState('')
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(false)
  const [saving, setSaving] = useState(false)
  const [serverError, setServerError] = useState('')
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    let cancelled = false
    getJSON('/api/employee/settings').then((res) => {
      if (cancelled) return
      if (res.ok && res.data) {
        setReject(String(res.data.auto_reject_threshold))
        setApprove(String(res.data.auto_approve_threshold))
      } else {
        setLoadError(true)
      }
      setLoading(false)
    })
    return () => {
      cancelled = true
    }
  }, [])

  function handleRejectChange(e) {
    setReject(e.target.value)
    setSaved(false)
  }

  function handleApproveChange(e) {
    setApprove(e.target.value)
    setSaved(false)
  }

  const rejectNum = toThresholdNumber(reject)
  const approveNum = toThresholdNumber(approve)
  // Полный диапазон 0–100 допустим, поэтому валидность = попадание в диапазон
  // и инвариант reject < approve (инвариант совпадает с проверкой бэкенда).
  const rejectValid = Number.isInteger(rejectNum) && rejectNum >= THRESHOLD.MIN && rejectNum <= THRESHOLD.MAX
  const approveValid = Number.isInteger(approveNum) && approveNum >= THRESHOLD.MIN && approveNum <= THRESHOLD.MAX
  const orderValid = rejectValid && approveValid && rejectNum < approveNum
  const formValid = rejectValid && approveValid && orderValid

  async function handleSubmit(e) {
    e.preventDefault()
    if (!formValid || saving) return

    setSaving(true)
    setServerError('')
    setSaved(false)

    const res = await putJSON('/api/employee/settings', {
      auto_reject_threshold: rejectNum,
      auto_approve_threshold: approveNum,
    })

    if (!res.ok) {
      setServerError(res.error || t('employeeSettings.saveError'))
    } else {
      setReject(String(res.data.auto_reject_threshold))
      setApprove(String(res.data.auto_approve_threshold))
      setSaved(true)
    }
    setSaving(false)
  }

  return (
    <div className="employeesettings-page">
      <div className="employeesettings-page__inner">
        <h1 className="employeesettings-page__title">{t('employeeSettings.title')}</h1>

        <div className="employeesettings-card">
          <h2 className="employeesettings-card__subtitle">{t('employeeSettings.automation')}</h2>

          {loading ? (
            <p className="employeesettings-loading">{t('employeeSettings.loading')}</p>
          ) : loadError ? (
            <p className="employeesettings-field__error">{t('employeeSettings.loadError')}</p>
          ) : (
            <form className="employeesettings-form" onSubmit={handleSubmit} noValidate>
              <p className="employeesettings-form__desc">{t('employeeSettings.desc')}</p>

              <div className="employeesettings-row">
                <div className="employeesettings-field">
                  <label className="employeesettings-field__label" htmlFor="reject">
                    {t('employeeSettings.reject')}
                  </label>
                  <input
                    className="employeesettings-field__input"
                    type="number"
                    id="reject"
                    name="reject"
                    min={THRESHOLD.MIN}
                    max={THRESHOLD.MAX}
                    step="1"
                    required
                    value={reject}
                    onChange={handleRejectChange}
                  />
                </div>

                <div className="employeesettings-field">
                  <label className="employeesettings-field__label" htmlFor="approve">
                    {t('employeeSettings.approve')}
                  </label>
                  <input
                    className="employeesettings-field__input"
                    type="number"
                    id="approve"
                    name="approve"
                    min={THRESHOLD.MIN}
                    max={THRESHOLD.MAX}
                    step="1"
                    required
                    value={approve}
                    onChange={handleApproveChange}
                  />
                </div>
              </div>

              {rejectValid && approveValid && !orderValid && (
                <p className="employeesettings-field__error">{t('employeeSettings.orderHint')}</p>
              )}

              {serverError && <p className="employeesettings-field__error">{serverError}</p>}
              {saved && !serverError && <p className="employeesettings-success">{t('employeeSettings.saved')}</p>}

              <button className="employeesettings-form__submit" type="submit" disabled={!formValid || saving}>
                {t('employeeSettings.save')}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
