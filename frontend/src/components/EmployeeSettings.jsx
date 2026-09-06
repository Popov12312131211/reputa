import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useBlocker } from 'react-router-dom'
import { Pencil, Eye, EyeOff } from 'lucide-react'
import { getJSON, putJSON } from '../api'
import { PHONE, PHONE_MASK, PASSWORD_RULES, TELEGRAM } from '../constants/auth'
import { THRESHOLD } from '../constants/threshold'
import { formatPhone, phoneIsValid, requiredIsValid } from '../utils/validators'
import './EmployeeSettings.css'

// Маска для read-only отображения полей пароля.
const MASK_PASSWORD = '••••••••'

// Мок текущих значений профиля сотрудника: реального сохранения на бэкенд
// пока нет (EMP-001 — только frontend), поэтому поля инициализированы
// заглушкой по типу APP-006/UserSettings.
const MOCK_PROFILE = {
  fullName: 'Петров Пётр Петрович',
  login: 'PetrPetrov1995',
  telegram: '@petr_petrov',
  phone: '+7(900)123-45-67',
}

const ICON_SIZE = 18

// Пустое поле — не число: Number('') === 0 неверно трактовал бы очищенное
// поле как порог 0, поэтому пустую строку отображаем в NaN (невалидно).
function toThresholdNumber(value) {
  if (value.trim() === '') return NaN
  return Number(value)
}

export default function EmployeeSettings() {
  const { t } = useTranslation()

  // savedValues — «сохранённый» снимок: по нему считаются несохранённые
  // изменения (dirty) и происходит отмена правок при выходе из режима
  // редактирования карандашом (тот же паттерн, что в UserSettings).
  const [savedValues, setSavedValues] = useState({
    ...MOCK_PROFILE,
    password: '',
    passwordConfirm: '',
  })
  const [values, setValues] = useState(savedValues)

  // Какое поле (или пара полей пароля — общий ключ password) сейчас
  // в режиме редактирования. По умолчанию всё read-only.
  const [editing, setEditing] = useState({
    fullName: false,
    login: false,
    telegram: false,
    phone: false,
    password: false,
  })
  const [touched, setTouched] = useState({})
  const [visible, setVisible] = useState({ password: false, passwordConfirm: false })

  const dirty = Object.keys(values).some((key) => values[key] !== savedValues[key])

  // Блокировка внутренней навигации по роутеру: когда есть несохранённые
  // изменения, useBlocker перехватывает переход и показывает свой confirm.
  const blocker = useBlocker(dirty)

  // Закрытие/обновление вкладки — стандартный браузерный confirm (beforeunload).
  useEffect(() => {
    if (!dirty) return undefined
    const onBeforeUnload = (e) => {
      e.preventDefault()
      e.returnValue = ''
    }
    window.addEventListener('beforeunload', onBeforeUnload)
    return () => window.removeEventListener('beforeunload', onBeforeUnload)
  }, [dirty])

  const passwordChecks = {}
  PASSWORD_RULES.forEach((rule) => {
    passwordChecks[rule.key] = rule.test(values.password)
  })
  const passwordOk = PASSWORD_RULES.every((rule) => rule.test(values.password))
  const passwordsMatch =
    values.password.length > 0 && values.password === values.passwordConfirm

  // Сохранение допустимо, только если все ИЗМЕНЁННЫЕ (dirty) поля валидны:
  // неизменённые поля уже прошли валидацию при предыдущем сохранении/загрузке.
  // Пара пароля проверяется вместе: правило сложности + совпадение, но только
  // если хотя бы одно из полей пары тронуто.
  const dirtyProfileFields = ['fullName', 'login', 'telegram', 'phone'].filter(
    (key) => values[key] !== savedValues[key],
  )
  const passwordDirty =
    values.password !== savedValues.password ||
    values.passwordConfirm !== savedValues.passwordConfirm
  const formValid =
    dirtyProfileFields.every((key) => validateField(key)) &&
    (!passwordDirty || (passwordOk && passwordsMatch))

  function setField(key, value) {
    setValues((prev) => ({ ...prev, [key]: value }))
  }

  function touchField(key) {
    setTouched((prev) => ({ ...prev, [key]: true }))
  }

  function validateField(key) {
    const v = values[key].trim()
    switch (key) {
      case 'fullName':
      case 'login':
        return requiredIsValid(v)
      case 'phone':
        return phoneIsValid(v)
      case 'telegram':
        return TELEGRAM.isValid(v)
      default:
        return true
    }
  }

  function toggleEdit(key) {
    if (editing[key]) {
      // Выход из режима редактирования без сохранения = отмена правок поля:
      // значение возвращается к последнему сохранённому снимку.
      setValues((prev) => ({ ...prev, [key]: savedValues[key] }))
      setEditing((prev) => ({ ...prev, [key]: false }))
      setTouched((prev) => ({ ...prev, [key]: false }))
    } else {
      setEditing((prev) => ({ ...prev, [key]: true }))
    }
  }

  function togglePasswordEdit() {
    if (editing.password) {
      setValues((prev) => ({
        ...prev,
        password: savedValues.password,
        passwordConfirm: savedValues.passwordConfirm,
      }))
      setEditing((prev) => ({ ...prev, password: false }))
      setTouched((prev) => ({ ...prev, password: false, passwordConfirm: false }))
      setVisible({ password: false, passwordConfirm: false })
    } else {
      setEditing((prev) => ({ ...prev, password: true }))
    }
  }

  function toggleVisible(field) {
    setVisible((prev) => ({ ...prev, [field]: !prev[field] }))
  }

  // Сохранение профиля — заглушка (backend EMP-001 не подключён): фиксируем
  // снимок, dirty обнуляется, кнопка «Сохранить» исчезает.
  function handleSave() {
    if (!formValid) return
    console.log('save employee profile (заглушка)')
    setSavedValues({ ...values })
    setTouched({})
  }

  function handleDeleteAccount() {
    console.log('delete account (заглушка)')
  }

  function handleLogout() {
    console.log('logout (заглушка)')
  }

  // Блок «Автоматизация» — реальная логика EMP-002: пороги читаются и
  // сохраняются через GET/PUT /api/employee/settings (бэкенд уже реализован).
  const [reject, setReject] = useState('')
  const [approve, setApprove] = useState('')
  const [autoLoading, setAutoLoading] = useState(true)
  const [autoLoadError, setAutoLoadError] = useState(false)
  const [autoSaving, setAutoSaving] = useState(false)
  const [autoServerError, setAutoServerError] = useState('')
  const [autoSaved, setAutoSaved] = useState(false)

  useEffect(() => {
    let cancelled = false
    getJSON('/api/employee/settings').then((res) => {
      if (cancelled) return
      if (res.ok && res.data) {
        setReject(String(res.data.auto_reject_threshold))
        setApprove(String(res.data.auto_approve_threshold))
      } else {
        setAutoLoadError(true)
      }
      setAutoLoading(false)
    })
    return () => {
      cancelled = true
    }
  }, [])

  function handleRejectChange(e) {
    setReject(e.target.value)
    setAutoSaved(false)
  }

  function handleApproveChange(e) {
    setApprove(e.target.value)
    setAutoSaved(false)
  }

  const rejectNum = toThresholdNumber(reject)
  const approveNum = toThresholdNumber(approve)
  // Полный диапазон 0–100 допустим, поэтому валидность = попадание в диапазон
  // и инвариант reject < approve (инвариант совпадает с проверкой бэкенда).
  const rejectValid = Number.isInteger(rejectNum) && rejectNum >= THRESHOLD.MIN && rejectNum <= THRESHOLD.MAX
  const approveValid = Number.isInteger(approveNum) && approveNum >= THRESHOLD.MIN && approveNum <= THRESHOLD.MAX
  const orderValid = rejectValid && approveValid && rejectNum < approveNum
  const autoFormValid = rejectValid && approveValid && orderValid

  async function handleAutoSubmit(e) {
    e.preventDefault()
    if (!autoFormValid || autoSaving) return

    setAutoSaving(true)
    setAutoServerError('')
    setAutoSaved(false)

    const res = await putJSON('/api/employee/settings', {
      auto_reject_threshold: rejectNum,
      auto_approve_threshold: approveNum,
    })

    if (!res.ok) {
      setAutoServerError(res.error || t('employeeSettings.saveError'))
    } else {
      setReject(String(res.data.auto_reject_threshold))
      setApprove(String(res.data.auto_approve_threshold))
      setAutoSaved(true)
    }
    setAutoSaving(false)
  }

  const inputClass = (key) =>
    `employeesettings-field__input${editing[key] ? ' employeesettings-field__input--editable' : ' employeesettings-field__input--readonly'}`

  const pencilClass = (key) =>
    `employeesettings-field__pencil${editing[key] ? ' employeesettings-field__pencil--active' : ''}`

  return (
    <div className="employeesettings-page">
      <div className="employeesettings-page__inner">
        <h1 className="employeesettings-page__title">{t('employeeSettings.title')}</h1>

        <section className="employeesettings-card">
          <h2 className="employeesettings-card__subtitle">{t('employeeSettings.basicTitle')}</h2>
          <div className="employeesettings-grid">
            <div className="employeesettings-field">
              <label className="employeesettings-field__label" htmlFor="fullName">
                {t('employeeSettings.fullName')}
              </label>
              <div className="employeesettings-field__wrap">
                <input
                  className={inputClass('fullName')}
                  type="text"
                  id="fullName"
                  value={values.fullName}
                  readOnly={!editing.fullName}
                  onChange={(e) => setField('fullName', e.target.value)}
                  onBlur={() => touchField('fullName')}
                />
                <button
                  className={pencilClass('fullName')}
                  type="button"
                  aria-label={t('employeeSettings.edit')}
                  title={t('employeeSettings.edit')}
                  onClick={() => toggleEdit('fullName')}
                >
                  <Pencil size={ICON_SIZE} strokeWidth={1.5} />
                </button>
              </div>
              {editing.fullName && touched.fullName && !validateField('fullName') && (
                <span className="employeesettings-field__error">{t('employeeSettings.required')}</span>
              )}
            </div>

            <div className="employeesettings-field">
              <label className="employeesettings-field__label" htmlFor="login">
                {t('employeeSettings.login')}
              </label>
              <div className="employeesettings-field__wrap">
                <input
                  className={inputClass('login')}
                  type="text"
                  id="login"
                  value={values.login}
                  readOnly={!editing.login}
                  onChange={(e) => setField('login', e.target.value)}
                  onBlur={() => touchField('login')}
                />
                <button
                  className={pencilClass('login')}
                  type="button"
                  aria-label={t('employeeSettings.edit')}
                  title={t('employeeSettings.edit')}
                  onClick={() => toggleEdit('login')}
                >
                  <Pencil size={ICON_SIZE} strokeWidth={1.5} />
                </button>
              </div>
              {editing.login && touched.login && !validateField('login') && (
                <span className="employeesettings-field__error">{t('employeeSettings.required')}</span>
              )}
            </div>

            <div className="employeesettings-field">
              <label className="employeesettings-field__label" htmlFor="telegram">
                {t('employeeSettings.telegram')}
              </label>
              <div className="employeesettings-field__wrap">
                <input
                  className={inputClass('telegram')}
                  type="text"
                  id="telegram"
                  placeholder="@username"
                  value={values.telegram}
                  readOnly={!editing.telegram}
                  onFocus={() => {
                    if (values.telegram === '') setField('telegram', '@')
                  }}
                  onChange={(e) => setField('telegram', TELEGRAM.format(e.target.value))}
                  onBlur={() => {
                    if (values.telegram === '@') setField('telegram', '')
                    touchField('telegram')
                  }}
                />
                <button
                  className={pencilClass('telegram')}
                  type="button"
                  aria-label={t('employeeSettings.edit')}
                  title={t('employeeSettings.edit')}
                  onClick={() => toggleEdit('telegram')}
                >
                  <Pencil size={ICON_SIZE} strokeWidth={1.5} />
                </button>
              </div>
              {editing.telegram && touched.telegram && !validateField('telegram') && (
                <span className="employeesettings-field__error">
                  {values.telegram.trim().length === 0
                    ? t('employeeSettings.required')
                    : t('employeeSettings.telegramHint')}
                </span>
              )}
            </div>

            <div className="employeesettings-field">
              <label className="employeesettings-field__label" htmlFor="phone">
                {t('employeeSettings.phone')}
              </label>
              <div className="employeesettings-field__wrap">
                <input
                  className={inputClass('phone')}
                  type="text"
                  id="phone"
                  placeholder={PHONE_MASK}
                  maxLength="16"
                  inputMode="numeric"
                  value={values.phone}
                  readOnly={!editing.phone}
                  onChange={(e) => setField('phone', formatPhone(e.target.value))}
                  onKeyDown={(e) => {
                    if ([8, 46, 37, 38, 39, 40, 9].includes(e.keyCode)) return
                    if (e.ctrlKey || e.metaKey) return
                    if (values.phone.replace(/\D/g, '').length >= PHONE.DIGITS) {
                      e.preventDefault()
                    }
                  }}
                  onBlur={() => touchField('phone')}
                />
                <button
                  className={pencilClass('phone')}
                  type="button"
                  aria-label={t('employeeSettings.edit')}
                  title={t('employeeSettings.edit')}
                  onClick={() => toggleEdit('phone')}
                >
                  <Pencil size={ICON_SIZE} strokeWidth={1.5} />
                </button>
              </div>
              {editing.phone && touched.phone && !validateField('phone') && (
                <span className="employeesettings-field__error">
                  {values.phone.replace(/\D/g, '').length === 0
                    ? t('employeeSettings.required')
                    : t('employeeSettings.phoneHint')}
                </span>
              )}
            </div>
          </div>
        </section>

        <section className="employeesettings-card">
          <h2 className="employeesettings-card__subtitle">{t('employeeSettings.securityTitle')}</h2>
          <div className="employeesettings-password">
            <div className="employeesettings-row">
              <div className="employeesettings-field">
                <label className="employeesettings-field__label" htmlFor="password">
                  {t('employeeSettings.password')}
                </label>
                <div className="employeesettings-field__wrap">
                  <input
                    className={`${inputClass('password')} employeesettings-field__input--password`}
                    type={visible.password ? 'text' : 'password'}
                    id="password"
                    value={editing.password ? values.password : MASK_PASSWORD}
                    readOnly={!editing.password}
                    onChange={(e) => setField('password', e.target.value)}
                  />
                  {editing.password && (
                    <button
                      className={`employeesettings-field__toggle${visible.password ? ' employeesettings-field__toggle--visible' : ''}`}
                      type="button"
                      aria-label={visible.password ? t('employeeSettings.hidePassword') : t('employeeSettings.showPassword')}
                      onClick={() => toggleVisible('password')}
                    >
                      <Eye className="employeesettings-field__eye employeesettings-field__eye--open" size={20} strokeWidth={1.5} />
                      <EyeOff className="employeesettings-field__eye employeesettings-field__eye--closed" size={20} strokeWidth={1.5} />
                    </button>
                  )}
                </div>
                <ul className="employeesettings-field__hint">
                  {PASSWORD_RULES.map((rule) => (
                    <li
                      key={rule.key}
                      className={passwordChecks[rule.key] ? 'employeesettings-field__hint--ok' : ''}
                    >
                      <span className="employeesettings-field__hint-icon">
                        {passwordChecks[rule.key] ? '\u2713' : '\u2022'}
                      </span>
                      {t(`employeeSettings.passwordRules.${rule.key}`)}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="employeesettings-field">
                <label className="employeesettings-field__label" htmlFor="passwordConfirm">
                  {t('employeeSettings.passwordConfirm')}
                </label>
                <div className="employeesettings-field__wrap">
                  <input
                    className={`${inputClass('password')} employeesettings-field__input--password`}
                    type={visible.passwordConfirm ? 'text' : 'password'}
                    id="passwordConfirm"
                    value={editing.password ? values.passwordConfirm : MASK_PASSWORD}
                    readOnly={!editing.password}
                    onChange={(e) => setField('passwordConfirm', e.target.value)}
                    onBlur={() => touchField('passwordConfirm')}
                  />
                  {editing.password && (
                    <button
                      className={`employeesettings-field__toggle${visible.passwordConfirm ? ' employeesettings-field__toggle--visible' : ''}`}
                      type="button"
                      aria-label={visible.passwordConfirm ? t('employeeSettings.hidePassword') : t('employeeSettings.showPassword')}
                      onClick={() => toggleVisible('passwordConfirm')}
                    >
                      <Eye className="employeesettings-field__eye employeesettings-field__eye--open" size={20} strokeWidth={1.5} />
                      <EyeOff className="employeesettings-field__eye employeesettings-field__eye--closed" size={20} strokeWidth={1.5} />
                    </button>
                  )}
                </div>
                {editing.password && touched.passwordConfirm && values.passwordConfirm.length > 0 && !passwordsMatch && (
                  <span className="employeesettings-field__error">{t('employeeSettings.passwordMismatch')}</span>
                )}
              </div>

              <div className="employeesettings-password__edit">
                <button
                  className={`employeesettings-password__pencil${editing.password ? ' employeesettings-password__pencil--active' : ''}`}
                  type="button"
                  aria-label={t('employeeSettings.edit')}
                  title={t('employeeSettings.edit')}
                  onClick={togglePasswordEdit}
                >
                  <Pencil size={ICON_SIZE} strokeWidth={1.5} />
                </button>
              </div>
            </div>
          </div>

          <div className="employeesettings-actions">
            <button
              className="employeesettings-actions__btn employeesettings-actions__btn--danger"
              type="button"
              onClick={handleDeleteAccount}
            >
              {t('employeeSettings.deleteAccount')}
            </button>
            <button
              className="employeesettings-actions__btn employeesettings-actions__btn--danger"
              type="button"
              onClick={handleLogout}
            >
              {t('employeeSettings.logout')}
            </button>
          </div>
        </section>

        <section className="employeesettings-card">
          <h2 className="employeesettings-card__subtitle">{t('employeeSettings.automation')}</h2>

          {autoLoading ? (
            <p className="employeesettings-loading">{t('employeeSettings.loading')}</p>
          ) : autoLoadError ? (
            <p className="employeesettings-field__error">{t('employeeSettings.loadError')}</p>
          ) : (
            <form className="employeesettings-form" onSubmit={handleAutoSubmit} noValidate>
              <p className="employeesettings-form__desc">{t('employeeSettings.desc')}</p>

              <div className="employeesettings-row">
                <div className="employeesettings-field">
                  <label className="employeesettings-field__label" htmlFor="reject">
                    {t('employeeSettings.reject')}
                  </label>
                  <input
                    className="employeesettings-field__input employeesettings-field__input--auto"
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
                    className="employeesettings-field__input employeesettings-field__input--auto"
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

              {autoServerError && <p className="employeesettings-field__error">{autoServerError}</p>}
              {autoSaved && !autoServerError && <p className="employeesettings-success">{t('employeeSettings.saved')}</p>}

              <button className="employeesettings-form__submit" type="submit" disabled={!autoFormValid || autoSaving}>
                {t('employeeSettings.saveThresholds')}
              </button>
            </form>
          )}
        </section>
      </div>

      {dirty && (
        <button
          className="employeesettings-save"
          type="button"
          disabled={!formValid}
          onClick={handleSave}
        >
          {t('employeeSettings.save')}
        </button>
      )}

      {blocker.state === 'blocked' && (
        <div className="employeesettings-confirm">
          <div className="employeesettings-confirm__box">
            <p className="employeesettings-confirm__title">{t('employeeSettings.confirmTitle')}</p>
            <p className="employeesettings-confirm__message">{t('employeeSettings.confirmMessage')}</p>
            <div className="employeesettings-confirm__actions">
              <button
                className="employeesettings-confirm__btn employeesettings-confirm__btn--stay"
                type="button"
                onClick={blocker.reset}
              >
                {t('employeeSettings.confirmStay')}
              </button>
              <button
                className="employeesettings-confirm__btn employeesettings-confirm__btn--leave"
                type="button"
                onClick={blocker.proceed}
              >
                {t('employeeSettings.confirmLeave')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
