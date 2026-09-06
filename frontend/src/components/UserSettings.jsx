import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useBlocker, useNavigate } from 'react-router-dom'
import { Pencil, Eye, EyeOff } from 'lucide-react'
import { getJSON, postJSON, patchJSON, deleteJSON } from '../api'
import { useAuth } from '../contexts/AuthContext'
import { PHONE, PHONE_MASK, PASSWORD_RULES, TELEGRAM } from '../constants/auth'
import { formatPhone, phoneIsValid, requiredIsValid } from '../utils/validators'
import './UserSettings.css'

// Маска для read-only отображения полей пароля.
const MASK_PASSWORD = '••••••••'

// Пустой профиль — стартовое значение до загрузки с бэкенда GET /auth/profile.
const EMPTY_PROFILE = {
  fullName: '',
  login: '',
  telegram: '',
  phone: '',
}

const ICON_SIZE = 18

export default function UserSettings() {
  const { t } = useTranslation()
  const { clearSession } = useAuth()
  const navigate = useNavigate()

  const [loadError, setLoadError] = useState(false)
  const [saveError, setSaveError] = useState('')
  const [saving, setSaving] = useState(false)

  // savedValues — «сохранённый» снимок: по нему считаются несохранённые
  // изменения (dirty) и происходит отмена правок при выходе из режима
  // редактирования карандашом.
  const [savedValues, setSavedValues] = useState({
    ...EMPTY_PROFILE,
    password: '',
    passwordConfirm: '',
  })
  const [values, setValues] = useState(savedValues)

  // Загрузка текущего профиля с бэкенда при монтировании.
  useEffect(() => {
    let cancelled = false
    getJSON('/api/auth/profile').then((res) => {
      if (cancelled) return
      if (!res.ok || !res.data) {
        setLoadError(true)
        return
      }
      // Телефон хранится на бэкенде в виде +79991234567; для поля настроек
      // приводим к той же маске, что использует страница регистрации.
      const phone = formatPhone(res.data.phone.replace(/\D/g, ''))
      const loaded = {
        fullName: res.data.full_name,
        login: res.data.login,
        telegram: res.data.telegram,
        phone,
        password: '',
        passwordConfirm: '',
      }
      setValues(loaded)
      setSavedValues(loaded)
    })
    return () => {
      cancelled = true
    }
  }, [])

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

  // Сохранение профиля: PATCH /api/auth/profile (APP-006B — реальный бэкенд).
  // Пароль отправляется только если пользователь его менял; остальные поля —
  // всегда. Телефон приводится к формату бэкенда +79991234567 (как в регистрации).
  async function handleSave() {
    if (!formValid || saving) return
    setSaving(true)
    setSaveError('')

    const passwordDirty =
      values.password !== savedValues.password ||
      values.passwordConfirm !== savedValues.passwordConfirm
    const body = {
      full_name: values.fullName.trim(),
      login: values.login.trim(),
      phone: `+${values.phone.replace(/\D/g, '')}`,
      telegram: values.telegram.trim(),
      password: passwordDirty ? values.password : null,
    }

    const res = await patchJSON('/api/auth/profile', body)
    setSaving(false)

    if (!res.ok) {
      setSaveError(res.error || t('userSettings.saveError'))
      return
    }

    setSavedValues({ ...values })
    setTouched({})
    setSaveError('')
  }

  async function handleLogout() {
    // Сбрасываем dirty заранее, чтобы on-beforeunload/useBlocker не перехватили
    // переход на /login после успешного выхода.
    setSavedValues({ ...values })
    const res = await postJSON('/api/auth/logout', {})
    clearSession()
    navigate('/login', { replace: true })
  }

  async function handleDeleteAccount() {
    setSavedValues({ ...values })
    const res = await deleteJSON('/api/auth/delete')
    clearSession()
    navigate('/login', { replace: true })
  }

  const inputClass = (key) =>
    `usersettings-field__input${editing[key] ? ' usersettings-field__input--editable' : ' usersettings-field__input--readonly'}`

  const pencilClass = (key) =>
    `usersettings-field__pencil${editing[key] ? ' usersettings-field__pencil--active' : ''}`

  return (
    <div className="usersettings-page">
      <div className="usersettings-page__inner">
        <h1 className="usersettings-page__title">{t('userSettings.title')}</h1>

        {loadError && <p className="usersettings-field__error">{t('userSettings.loadError')}</p>}

        <section className="usersettings-card">
          <h2 className="usersettings-card__subtitle">{t('userSettings.basicTitle')}</h2>
          <div className="usersettings-grid">
            <div className="usersettings-field">
              <label className="usersettings-field__label" htmlFor="fullName">
                {t('userSettings.fullName')}
              </label>
              <div className="usersettings-field__wrap">
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
                  aria-label={t('userSettings.edit')}
                  title={t('userSettings.edit')}
                  onClick={() => toggleEdit('fullName')}
                >
                  <Pencil size={ICON_SIZE} strokeWidth={1.5} />
                </button>
              </div>
              {editing.fullName && touched.fullName && !validateField('fullName') && (
                <span className="usersettings-field__error">{t('userSettings.required')}</span>
              )}
            </div>

            <div className="usersettings-field">
              <label className="usersettings-field__label" htmlFor="login">
                {t('userSettings.login')}
              </label>
              <div className="usersettings-field__wrap">
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
                  aria-label={t('userSettings.edit')}
                  title={t('userSettings.edit')}
                  onClick={() => toggleEdit('login')}
                >
                  <Pencil size={ICON_SIZE} strokeWidth={1.5} />
                </button>
              </div>
              {editing.login && touched.login && !validateField('login') && (
                <span className="usersettings-field__error">{t('userSettings.required')}</span>
              )}
            </div>

            <div className="usersettings-field">
              <label className="usersettings-field__label" htmlFor="telegram">
                {t('userSettings.telegram')}
              </label>
              <div className="usersettings-field__wrap">
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
                  aria-label={t('userSettings.edit')}
                  title={t('userSettings.edit')}
                  onClick={() => toggleEdit('telegram')}
                >
                  <Pencil size={ICON_SIZE} strokeWidth={1.5} />
                </button>
              </div>
              {editing.telegram && touched.telegram && !validateField('telegram') && (
                <span className="usersettings-field__error">
                  {values.telegram.trim().length === 0
                    ? t('userSettings.required')
                    : t('userSettings.telegramHint')}
                </span>
              )}
            </div>

            <div className="usersettings-field">
              <label className="usersettings-field__label" htmlFor="phone">
                {t('userSettings.phone')}
              </label>
              <div className="usersettings-field__wrap">
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
                  aria-label={t('userSettings.edit')}
                  title={t('userSettings.edit')}
                  onClick={() => toggleEdit('phone')}
                >
                  <Pencil size={ICON_SIZE} strokeWidth={1.5} />
                </button>
              </div>
              {editing.phone && touched.phone && !validateField('phone') && (
                <span className="usersettings-field__error">
                  {values.phone.replace(/\D/g, '').length === 0
                    ? t('userSettings.required')
                    : t('userSettings.phoneHint')}
                </span>
              )}
            </div>
          </div>
        </section>

        <section className="usersettings-card">
          <h2 className="usersettings-card__subtitle">{t('userSettings.securityTitle')}</h2>
          <div className="usersettings-password">
            <div className="usersettings-row">
              <div className="usersettings-field">
                <label className="usersettings-field__label" htmlFor="password">
                  {t('userSettings.password')}
                </label>
                <div className="usersettings-field__wrap">
                  <input
                    className={`${inputClass('password')} usersettings-field__input--password`}
                    type={visible.password ? 'text' : 'password'}
                    id="password"
                    value={editing.password ? values.password : MASK_PASSWORD}
                    readOnly={!editing.password}
                    onChange={(e) => setField('password', e.target.value)}
                  />
                  {editing.password && (
                    <button
                      className={`usersettings-field__toggle${visible.password ? ' usersettings-field__toggle--visible' : ''}`}
                      type="button"
                      aria-label={visible.password ? t('userSettings.hidePassword') : t('userSettings.showPassword')}
                      onClick={() => toggleVisible('password')}
                    >
                      <Eye className="usersettings-field__eye usersettings-field__eye--open" size={20} strokeWidth={1.5} />
                      <EyeOff className="usersettings-field__eye usersettings-field__eye--closed" size={20} strokeWidth={1.5} />
                    </button>
                  )}
                </div>
                <ul className="usersettings-field__hint">
                  {PASSWORD_RULES.map((rule) => (
                    <li
                      key={rule.key}
                      className={passwordChecks[rule.key] ? 'usersettings-field__hint--ok' : ''}
                    >
                      <span className="usersettings-field__hint-icon">
                        {passwordChecks[rule.key] ? '\u2713' : '\u2022'}
                      </span>
                      {t(`userSettings.passwordRules.${rule.key}`)}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="usersettings-field">
                <label className="usersettings-field__label" htmlFor="passwordConfirm">
                  {t('userSettings.passwordConfirm')}
                </label>
                <div className="usersettings-field__wrap">
                  <input
                    className={`${inputClass('password')} usersettings-field__input--password`}
                    type={visible.passwordConfirm ? 'text' : 'password'}
                    id="passwordConfirm"
                    value={editing.password ? values.passwordConfirm : MASK_PASSWORD}
                    readOnly={!editing.password}
                    onChange={(e) => setField('passwordConfirm', e.target.value)}
                    onBlur={() => touchField('passwordConfirm')}
                  />
                  {editing.password && (
                    <button
                      className={`usersettings-field__toggle${visible.passwordConfirm ? ' usersettings-field__toggle--visible' : ''}`}
                      type="button"
                      aria-label={visible.passwordConfirm ? t('userSettings.hidePassword') : t('userSettings.showPassword')}
                      onClick={() => toggleVisible('passwordConfirm')}
                    >
                      <Eye className="usersettings-field__eye usersettings-field__eye--open" size={20} strokeWidth={1.5} />
                      <EyeOff className="usersettings-field__eye usersettings-field__eye--closed" size={20} strokeWidth={1.5} />
                    </button>
                  )}
                </div>
                {editing.password && touched.passwordConfirm && values.passwordConfirm.length > 0 && !passwordsMatch && (
                  <span className="usersettings-field__error">{t('userSettings.passwordMismatch')}</span>
                )}
              </div>

              <div className="usersettings-password__edit">
                <button
                  className={`usersettings-password__pencil${editing.password ? ' usersettings-password__pencil--active' : ''}`}
                  type="button"
                  aria-label={t('userSettings.edit')}
                  title={t('userSettings.edit')}
                  onClick={togglePasswordEdit}
                >
                  <Pencil size={ICON_SIZE} strokeWidth={1.5} />
                </button>
              </div>
            </div>
          </div>

          <div className="usersettings-actions">
            <button
              className="usersettings-actions__btn usersettings-actions__btn--danger"
              type="button"
              onClick={handleDeleteAccount}
            >
              {t('userSettings.deleteAccount')}
            </button>
            <button
              className="usersettings-actions__btn usersettings-actions__btn--danger"
              type="button"
              onClick={handleLogout}
            >
              {t('userSettings.logout')}
            </button>
          </div>
        </section>
      </div>

      {dirty && (
        <button
          className="usersettings-save"
          type="button"
          disabled={!formValid || saving}
          onClick={handleSave}
        >
          {saving ? t('userSettings.saving') : t('userSettings.save')}
        </button>
      )}
      {saveError && !dirty && <p className="usersettings-field__error">{saveError}</p>}

      {blocker.state === 'blocked' && (
        <div className="usersettings-confirm">
          <div className="usersettings-confirm__box">
            <p className="usersettings-confirm__title">{t('userSettings.confirmTitle')}</p>
            <p className="usersettings-confirm__message">{t('userSettings.confirmMessage')}</p>
            <div className="usersettings-confirm__actions">
              <button
                className="usersettings-confirm__btn usersettings-confirm__btn--stay"
                type="button"
                onClick={blocker.reset}
              >
                {t('userSettings.confirmStay')}
              </button>
              <button
                className="usersettings-confirm__btn usersettings-confirm__btn--leave"
                type="button"
                onClick={blocker.proceed}
              >
                {t('userSettings.confirmLeave')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}