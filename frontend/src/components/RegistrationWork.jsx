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
  EMPLOYEE_IDENTIFIER,
} from '../constants/auth'
import { requiredIsValid, phoneIsValid, formatPhone } from '../utils/validators'
import './RegistrationWork.css'

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

function formatDate(value) {
  const digits = value.replace(/\D/g, '').slice(0, 8)
  let formatted = ''
  if (digits.length > 0) formatted = digits.slice(0, 2)
  if (digits.length > 2) formatted += '.' + digits.slice(2, 4)
  if (digits.length > 4) formatted += '.' + digits.slice(4, 8)
  return formatted
}

export default function RegistrationWork() {
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
    identifier: '',
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
        return requiredIsValid(v)
      case 'phone':
        return phoneIsValid(v)
      case 'telegram':
        return TELEGRAM.isValid(v)
      case 'identifier':
        return EMPLOYEE_IDENTIFIER.isValid(v)
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
    validateField('telegram') &&
    validateField('identifier')

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

    const result = await postJSON('/api/auth/register/employee', {
      full_name: values.fullName.trim(),
      birth_date: `${year}-${month}-${day}`,
      login: values.login.trim(),
      password: values.password,
      phone: `+${phoneDigits}`,
      telegram: values.telegram.trim(),
      identifier: values.identifier.trim(),
    })

    if (!result.ok) {
      setServerError(result.error || t('registrationWork.error'))
      return
    }

    navigate('/loginWork')
  }

  function toggleVisible(field) {
    setVisible((prev) => ({ ...prev, [field]: !prev[field] }))
  }

  return (
    <div className="registrationwork-page">
      <div className="registrationwork-page__inner">
      <div className="registrationwork-card">
        <span className="registrationwork-card__logo">{t('registrationWork.logo')}</span>

        <form className="registrationwork-form" onSubmit={handleSubmit} noValidate>
          <div className="registrationwork-field">
            <label className="registrationwork-field__label" htmlFor="fullName">
              {t('registrationWork.fullName')}
            </label>
            <input
              className="registrationwork-field__input"
              type="text"
              id="fullName"
              name="fullName"
              placeholder={t('registrationWork.fullNamePlaceholder')}
              required
              value={values.fullName}
              onChange={(e) => setField('fullName', e.target.value)}
              onBlur={() => setTouched((prev) => ({ ...prev, fullName: true }))}
            />
            {touched.fullName && !validateField('fullName') && (
              <span className="registrationwork-field__error">{t('registrationWork.fullNameHint')}</span>
            )}
          </div>

          <div className="registrationwork-field">
            <label className="registrationwork-field__label" htmlFor="identifier">
              {t('registrationWork.identifier')}
            </label>
            <input
              className={`registrationwork-field__input${touched.identifier && !validateField('identifier') ? ' registrationwork-field__input--error' : ''}`}
              type="text"
              id="identifier"
              name="identifier"
              placeholder="A123room19"
              maxLength="10"
              required
              value={values.identifier}
              onChange={(e) => setField('identifier', EMPLOYEE_IDENTIFIER.format(e.target.value))}
              onBlur={() => setTouched((prev) => ({ ...prev, identifier: true }))}
            />
            {touched.identifier && !validateField('identifier') && (
              <span className="registrationwork-field__error">
                {values.identifier.trim().length === 0
                  ? t('registrationWork.required')
                  : t('registrationWork.identifierError')}
              </span>
            )}
          </div>

          <div className="registrationwork-field">
            <label className="registrationwork-field__label" htmlFor="birthDate">
              {t('registrationWork.birthDate')}
            </label>
            <input
              className={`registrationwork-field__input${touched.birthDate && !dateIsValid(values.birthDate) ? ' registrationwork-field__input--error' : ''}`}
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
              <span className="registrationwork-field__error">
                {values.birthDate.trim().length === 0
                  ? t('registrationWork.required')
                  : t('registrationWork.birthDateHint')}
              </span>
            )}
          </div>

          <div className="registrationwork-field">
            <label className="registrationwork-field__label" htmlFor="login">
              {t('registrationWork.login')}
            </label>
            <input
              className={`registrationwork-field__input${touched.login && !validateField('login') ? ' registrationwork-field__input--error' : ''}`}
              type="text"
              id="login"
              name="login"
              placeholder={t('registrationWork.loginPlaceholder')}
              required
              value={values.login}
              onChange={(e) => setField('login', e.target.value)}
              onBlur={() => setTouched((prev) => ({ ...prev, login: true }))}
            />
            {touched.login && !validateField('login') && (
              <span className="registrationwork-field__error">{t('registrationWork.required')}</span>
            )}
          </div>

          <div className="registrationwork-field">
            <label className="registrationwork-field__label" htmlFor="password">
              {t('registrationWork.password')}
            </label>
            <div className="registrationwork-field__wrap">
              <input
                className={`registrationwork-field__input registrationwork-field__input--password${touched.password && !passwordOk ? ' registrationwork-field__input--error' : ''}`}
                type={visible.password ? 'text' : 'password'}
                id="password"
                name="password"
                required
                value={values.password}
                onChange={(e) => setField('password', e.target.value)}
                onBlur={() => setTouched((prev) => ({ ...prev, password: true }))}
              />
              <button
                className={`registrationwork-field__toggle${visible.password ? ' registrationwork-field__toggle--visible' : ''}`}
                type="button"
                aria-label={visible.password ? t('registrationWork.hidePassword') : t('registrationWork.showPassword')}
                onClick={() => toggleVisible('password')}
              >
                <svg className="registrationwork-field__eye registrationwork-field__eye--open" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                <svg className="registrationwork-field__eye registrationwork-field__eye--closed" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
              </button>
            </div>
            <ul className="registrationwork-field__hint">
              {PASSWORD_RULES.map((rule) => (
                <li
                  key={rule.key}
                  className={passwordChecks[rule.key] ? 'registrationwork-field__hint--ok' : ''}
                >
                  <span className="registrationwork-field__hint-icon">
                    {passwordChecks[rule.key] ? '\u2713' : '\u2022'}
                  </span>
                  {t(`registrationWork.passwordRules.${rule.key}`)}
                </li>
              ))}
            </ul>
          </div>

          <div className="registrationwork-field">
            <label className="registrationwork-field__label" htmlFor="passwordConfirm">
              {t('registrationWork.passwordConfirm')}
            </label>
            <div className="registrationwork-field__wrap">
              <input
                className={`registrationwork-field__input registrationwork-field__input--password${touched.passwordConfirm && !passwordsMatch ? ' registrationwork-field__input--error' : ''}`}
                type={visible.passwordConfirm ? 'text' : 'password'}
                id="passwordConfirm"
                name="passwordConfirm"
                required
                value={values.passwordConfirm}
                onChange={(e) => setField('passwordConfirm', e.target.value)}
                onBlur={() => setTouched((prev) => ({ ...prev, passwordConfirm: true }))}
              />
              <button
                className={`registrationwork-field__toggle${visible.passwordConfirm ? ' registrationwork-field__toggle--visible' : ''}`}
                type="button"
                aria-label={visible.passwordConfirm ? t('registrationWork.hidePassword') : t('registrationWork.showPassword')}
                onClick={() => toggleVisible('passwordConfirm')}
              >
                <svg className="registrationwork-field__eye registrationwork-field__eye--open" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                <svg className="registrationwork-field__eye registrationwork-field__eye--closed" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
              </button>
            </div>
            {touched.passwordConfirm && !passwordsMatch && (
              <span className="registrationwork-field__error">{t('registrationWork.passwordMismatch')}</span>
            )}
          </div>

          <div className="registrationwork-field">
            <label className="registrationwork-field__label" htmlFor="phone">
              {t('registrationWork.phone')}
            </label>
            <input
              className={`registrationwork-field__input${touched.phone && !validateField('phone') ? ' registrationwork-field__input--error' : ''}`}
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
              <span className="registrationwork-field__error">
                {values.phone.replace(/\D/g, '').length === 0
                  ? t('registrationWork.required')
                  : t('registrationWork.phoneHint')}
              </span>
            )}
          </div>

          <div className="registrationwork-field">
            <label className="registrationwork-field__label" htmlFor="telegram">
              {t('registrationWork.telegram')}
            </label>
            <input
              className={`registrationwork-field__input${touched.telegram && !validateField('telegram') ? ' registrationwork-field__input--error' : ''}`}
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
              <span className="registrationwork-field__error">
                {values.telegram.trim().length === 0
                  ? t('registrationWork.required')
                  : t('registrationWork.telegramHint')}
              </span>
            )}
          </div>

          <button className="registrationwork-form__submit" type="submit" disabled={!formValid}>
            {t('registrationWork.submit')}
          </button>
        </form>

        {serverError && (
          <p className="registrationwork-field__error" style={{ marginTop: 12 }}>
            {serverError}
          </p>
        )}

        <p className="registrationwork-card__login">
          {t('registrationWork.haveAccount')}{' '}
          <Link className="registrationwork-card__login-link" to="/loginWork">
            {t('registrationWork.loginLink')}
          </Link>
        </p>
      </div>
      {SHOW_AUTH_ILLUSTRATION && (
        <img className="registrationwork-page__illustration" src="/img/loginWork.jpg" alt="" />
      )}
      </div>
    </div>
  )
}
