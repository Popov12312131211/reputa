import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import './Login.css'

export default function Login() {
  const { t } = useTranslation()

  const [login, setLogin] = useState('')
  const [password, setPassword] = useState('')
  const [passwordVisible, setPasswordVisible] = useState(false)
  const [touched, setTouched] = useState({})
  const [serverError, setServerError] = useState('')

  const loginValid = login.trim().length > 0
  const passwordValid = password.length > 0
  const formValid = loginValid && passwordValid

  function handleSubmit(e) {
    e.preventDefault()
    setTouched({ login: true, password: true })

    if (!formValid) return

    setServerError('')
    // TODO: отправка на AUTH-002 (backend ещё не реализован)
    setServerError(t('login.serverNotReady'))
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <span className="login-card__logo">{t('login.logo')}</span>

        <form className="login-form" onSubmit={handleSubmit} noValidate>
          <div className="login-field">
            <label className="login-field__label" htmlFor="login">
              {t('login.login')}
            </label>
            <input
              className={`login-field__input${touched.login && !loginValid ? ' login-field__input--error' : ''}`}
              type="text"
              id="login"
              name="login"
              placeholder={t('login.loginPlaceholder')}
              required
              value={login}
              onChange={(e) => setLogin(e.target.value)}
              onBlur={() => setTouched((prev) => ({ ...prev, login: true }))}
            />
            {touched.login && !loginValid && (
              <span className="login-field__error">{t('login.required')}</span>
            )}
          </div>

          <div className="login-field">
            <label className="login-field__label" htmlFor="password">
              {t('login.password')}
            </label>
            <div className="login-field__wrap">
              <input
                className={`login-field__input login-field__input--password${touched.password && !passwordValid ? ' login-field__input--error' : ''}`}
                type={passwordVisible ? 'text' : 'password'}
                id="password"
                name="password"
                placeholder={t('login.passwordPlaceholder')}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onBlur={() => setTouched((prev) => ({ ...prev, password: true }))}
              />
              <button
                className={`login-field__toggle${passwordVisible ? ' login-field__toggle--visible' : ''}`}
                type="button"
                aria-label={passwordVisible ? t('login.hidePassword') : t('login.showPassword')}
                onClick={() => setPasswordVisible((v) => !v)}
              >
                <svg className="login-field__eye login-field__eye--open" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                <svg className="login-field__eye login-field__eye--closed" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
              </button>
            </div>
            {touched.password && !passwordValid && (
              <span className="login-field__error">{t('login.required')}</span>
            )}
          </div>

          <button className="login-form__submit" type="submit" disabled={!formValid}>
            {t('login.submit')}
          </button>
        </form>

        {serverError && (
          <p className="login-field__error" style={{ marginTop: 12 }}>
            {serverError}
          </p>
        )}

        <div className="login-card__links">
          <Link className="login-card__link" to="/forgot">
            {t('login.forgotPassword')}
          </Link>
          <p className="login-card__no-account">
            {t('login.noAccount')}{' '}
            <Link className="login-card__link" to="/registration">
              {t('login.registerLink')}
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
