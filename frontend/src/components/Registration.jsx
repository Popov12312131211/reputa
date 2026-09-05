import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'
import { postJSON } from '../api'
import {
  SHOW_AUTH_ILLUSTRATION,
  PASSWORD_RULES,
  PHONE_MASK,
  PHONE,
  DATE,
  TELEGRAM,
} from '../constants/auth'
import './Registration.css'

function fullNameIsValid(value) {
  const words = value.trim().split(/\s+/).filter(Boolean)
  return words.length >= 3
}

function dateIsValid(value) {
  const match = /^(\d{2})\.(\d{2})\.(\d{4})$/.exec(value.trim())
  if (!match) return false
  const day = parseInt(match[1], 10)
  const month = parseInt(match[2], 10)
  const year = parseInt(match[3], 10)

  if (day < 1 || day > 31 || month < 1 || month > 12) return false
  if (year < DATE.MIN_YEAR || year > new Date().getFullYear()) return false

  const date = new Date(year, month - 1, day)
  if (date.getDate() !== day || date.getMonth() !== month - 1 || date.getFullYear() !== year) {
    return false
  }

  const today = new Date()
  const todayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  const age = todayStart.getFullYear() - year - (
    todayStart.getMonth() < month - 1 ||
    (todayStart.getMonth() === month - 1 && todayStart.getDate() < day) ? 1 : 0
  )
  return age >= DATE.MIN_AGE
}

function loginIsValid(value) {
  return value.trim().length > 0
}

function phoneIsValid(value) {
  return value.replace(/\D/g, '').length === PHONE.DIGITS
}

function formatPhone(digits) {
  let d = digits.replace(/\D/g, '')
  if (d.length > 0 && d[0] === '8') d = '7' + d.slice(1)
  if (d.length > 0 && d[0] !== '7') d = '7' + d
  d = d.slice(0, 11)

  let formatted = '+7'
  if (d.length > 1) formatted += '(' + d.slice(1, 4)
  if (d.length >= 4) formatted += ')'
  if (d.length > 4) formatted += d.slice(4, 7)
  if (d.length > 7) formatted += '-' + d.slice(7, 9)
  if (d.length > 9) formatted += '-' + d.slice(9, 11)
  return formatted
}

function formatDate(value) {
  const digits = value.replace(/\D/g, '').slice(0, 8)
  let formatted = ''
  if (digits.length > 0) formatted = digits.slice(0, 2)
  if (digits.length > 2) formatted += '.' + digits.slice(2, 4)
  if (digits.length > 4) formatted += '.' + digits.slice(4, 8)
  return formatted
}

export default function Registration() {
  const { t } = useTranslation()
  const navigate = useNavigate()

  const [values, setValues] = useState({
    fullName: '',
    birthDate: '',
    login: '',
    password: '',
    passwordConfirm: '',
    phone: '',
    telegram: '',
  })
  const [visible, setVisible] = useState({ password: false, passwordConfirm: false })
  const [touched, setTouched] = useState({})
  const [serverError, setServerError] = useState('')

  const passwordChecks = {}
  PASSWORD_RULES.forEach((rule) => {
    passwordChecks[rule.key] = rule.test(values.password)
  })
  const passwordOk = PASSWORD_RULES.every((rule) => rule.test(values.password))
  const passwordsMatch =
    values.passwordConfirm.length > 0 && values.password === values.passwordConfirm

  function setField(field, value) {
    setValues((prev) => ({ ...prev, [field]: value }))
  }

  function validateField(field) {
    const v = values[field].trim()
    switch (field) {
      case 'fullName':
        return fullNameIsValid(v)
      case 'birthDate':
        return dateIsValid(v)
      case 'login':
        return loginIsValid(v)
      case 'phone':
        return phoneIsValid(v)
      case 'telegram':
        return TELEGRAM.isValid(v)
      default:
        return true
    }
  }

  const formValid =
    validateField('fullName') &&
    validateField('birthDate') &&
    validateField('login') &&
    passwordOk &&
    passwordsMatch &&
    validateField('phone') &&
    validateField('telegram')

  async function handleSubmit(e) {
    e.preventDefault()
    const allTouched = Object.keys(values).reduce((acc, key) => {
      acc[key] = true
      return acc
    }, {})
    setTouched(allTouched)

    if (!formValid) return

    setServerError('')

    const [day, month, year] = values.birthDate.split('.')
    const phoneDigits = values.phone.replace(/\D/g, '')

    const result = await postJSON('/api/auth/register', {
      full_name: values.fullName.trim(),
      birth_date: `${year}-${month}-${day}`,
      login: values.login.trim(),
      password: values.password,
      phone: `+${phoneDigits}`,
      telegram: values.telegram.trim(),
    })

    if (!result.ok) {
      setServerError(result.error || t('registration.error'))
      return
    }

    navigate('/login')
  }

  function toggleVisible(field) {
    setVisible((prev) => ({ ...prev, [field]: !prev[field] }))
  }

  return (
    <div className="registration-page">
      <div className="registration-page__inner">
      <div className="registration-card">
        <span className="registration-card__logo">{t('registration.logo')}</span>

        <form className="registration-form" onSubmit={handleSubmit} noValidate>
          <div className="registration-field">
            <label className="registration-field__label" htmlFor="fullName">
              {t('registration.fullName')}
            </label>
            <input
              className="registration-field__input"
              type="text"
              id="fullName"
              name="fullName"
              placeholder={t('registration.fullNamePlaceholder')}
              required
              value={values.fullName}
              onChange={(e) => setField('fullName', e.target.value)}
              onBlur={() => setTouched((prev) => ({ ...prev, fullName: true }))}
            />
            {touched.fullName && !validateField('fullName') && (
              <span className="registration-field__error">{t('registration.fullNameHint')}</span>
            )}
          </div>

          <div className="registration-field">
            <label className="registration-field__label" htmlFor="birthDate">
              {t('registration.birthDate')}
            </label>
            <input
              className={`registration-field__input${touched.birthDate && !dateIsValid(values.birthDate) ? ' registration-field__input--error' : ''}`}
              type="text"
              id="birthDate"
              name="birthDate"
              placeholder="дд.мм.гггг"
              maxLength="10"
              inputMode="numeric"
              required
              value={values.birthDate}
              onChange={(e) => setField('birthDate', formatDate(e.target.value))}
              onBlur={() => setTouched((prev) => ({ ...prev, birthDate: true }))}
            />
            {touched.birthDate && !dateIsValid(values.birthDate) && (
              <span className="registration-field__error">
                {values.birthDate.trim().length === 0
                  ? t('registration.required')
                  : t('registration.birthDateHint')}
              </span>
            )}
          </div>

          <div className="registration-field">
            <label className="registration-field__label" htmlFor="login">
              {t('registration.login')}
            </label>
            <input
              className={`registration-field__input${touched.login && !validateField('login') ? ' registration-field__input--error' : ''}`}
              type="text"
              id="login"
              name="login"
              placeholder={t('registration.loginPlaceholder')}
              required
              value={values.login}
              onChange={(e) => setField('login', e.target.value)}
              onBlur={() => setTouched((prev) => ({ ...prev, login: true }))}
            />
            {touched.login && !validateField('login') && (
              <span className="registration-field__error">{t('registration.required')}</span>
            )}
          </div>

          <div className="registration-field">
            <label className="registration-field__label" htmlFor="password">
              {t('registration.password')}
            </label>
            <div className="registration-field__wrap">
              <input
                className={`registration-field__input registration-field__input--password${touched.password && !passwordOk ? ' registration-field__input--error' : ''}`}
                type={visible.password ? 'text' : 'password'}
                id="password"
                name="password"
                required
                value={values.password}
                onChange={(e) => setField('password', e.target.value)}
                onBlur={() => setTouched((prev) => ({ ...prev, password: true }))}
              />
              <button
                className={`registration-field__toggle${visible.password ? ' registration-field__toggle--visible' : ''}`}
                type="button"
                aria-label={visible.password ? t('registration.hidePassword') : t('registration.showPassword')}
                onClick={() => toggleVisible('password')}
              >
                <svg className="registration-field__eye registration-field__eye--open" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                <svg className="registration-field__eye registration-field__eye--closed" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
              </button>
            </div>
            <ul className="registration-field__hint">
              {PASSWORD_RULES.map((rule) => (
                <li
                  key={rule.key}
                  className={passwordChecks[rule.key] ? 'registration-field__hint--ok' : ''}
                >
                  <span className="registration-field__hint-icon">
                    {passwordChecks[rule.key] ? '\u2713' : '\u2022'}
                  </span>
                  {t(`registration.passwordRules.${rule.key}`)}
                </li>
              ))}
            </ul>
          </div>

          <div className="registration-field">
            <label className="registration-field__label" htmlFor="passwordConfirm">
              {t('registration.passwordConfirm')}
            </label>
            <div className="registration-field__wrap">
              <input
                className={`registration-field__input registration-field__input--password${touched.passwordConfirm && !passwordsMatch ? ' registration-field__input--error' : ''}`}
                type={visible.passwordConfirm ? 'text' : 'password'}
                id="passwordConfirm"
                name="passwordConfirm"
                required
                value={values.passwordConfirm}
                onChange={(e) => setField('passwordConfirm', e.target.value)}
                onBlur={() => setTouched((prev) => ({ ...prev, passwordConfirm: true }))}
              />
              <button
                className={`registration-field__toggle${visible.passwordConfirm ? ' registration-field__toggle--visible' : ''}`}
                type="button"
                aria-label={visible.passwordConfirm ? t('registration.hidePassword') : t('registration.showPassword')}
                onClick={() => toggleVisible('passwordConfirm')}
              >
                <svg className="registration-field__eye registration-field__eye--open" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                <svg className="registration-field__eye registration-field__eye--closed" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
              </button>
            </div>
            {touched.passwordConfirm && !passwordsMatch && (
              <span className="registration-field__error">{t('registration.passwordMismatch')}</span>
            )}
          </div>

          <div className="registration-field">
            <label className="registration-field__label" htmlFor="phone">
              {t('registration.phone')}
            </label>
            <input
              className={`registration-field__input${touched.phone && !validateField('phone') ? ' registration-field__input--error' : ''}`}
              type="tel"
              id="phone"
              name="phone"
              placeholder={PHONE_MASK}
              maxLength="16"
              inputMode="numeric"
              required
              value={values.phone}
              onChange={(e) => setField('phone', formatPhone(e.target.value))}
              onKeyDown={(e) => {
                if ([8, 46, 37, 38, 39, 40, 9].includes(e.keyCode)) return
                if (e.ctrlKey || e.metaKey) return
                if (values.phone.replace(/\D/g, '').length >= PHONE.DIGITS) {
                  e.preventDefault()
                }
              }}
              onBlur={() => setTouched((prev) => ({ ...prev, phone: true }))}
            />
            {touched.phone && !validateField('phone') && (
              <span className="registration-field__error">
                {values.phone.replace(/\D/g, '').length === 0
                  ? t('registration.required')
                  : t('registration.phoneHint')}
              </span>
            )}
          </div>

          <div className="registration-field">
            <label className="registration-field__label" htmlFor="telegram">
              {t('registration.telegram')}
            </label>
            <input
              className={`registration-field__input${touched.telegram && !validateField('telegram') ? ' registration-field__input--error' : ''}`}
              type="text"
              id="telegram"
              name="telegram"
              placeholder="@username"
              required
              value={values.telegram}
              onChange={(e) => setField('telegram', TELEGRAM.format(e.target.value))}
              onFocus={() => {
                if (!values.telegram) setField('telegram', '@')
              }}
              onBlur={() => {
                if (values.telegram === '@') setField('telegram', '')
                setTouched((prev) => ({ ...prev, telegram: true }))
              }}
            />
            {touched.telegram && !validateField('telegram') && (
              <span className="registration-field__error">
                {values.telegram.trim().length === 0
                  ? t('registration.required')
                  : t('registration.telegramHint')}
              </span>
            )}
          </div>

          <button className="registration-form__submit" type="submit" disabled={!formValid}>
            {t('registration.submit')}
          </button>
        </form>

        {serverError && (
          <p className="registration-field__error" style={{ marginTop: 12 }}>
            {serverError}
          </p>
        )}

        <p className="registration-card__login">
          {t('registration.haveAccount')}{' '}
          <Link className="registration-card__login-link" to="/login">
            {t('registration.loginLink')}
          </Link>
        </p>
      </div>
      {SHOW_AUTH_ILLUSTRATION && (
        <img className="registration-page__illustration" src="/img/reg.jpg" alt="" />
      )}
      </div>
    </div>
  )
}
