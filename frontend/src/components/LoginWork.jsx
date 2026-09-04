import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import './LoginWork.css'

export default function LoginWork() {
  const { t } = useTranslation()

  const [login, setLogin] = useState('')
  const [code, setCode] = useState('')
  const [password, setPassword] = useState('')
  const [passwordVisible, setPasswordVisible] = useState(false)
  const [touched, setTouched] = useState({})
  const [serverError, setServerError] = useState('')

  const loginValid = login.trim().length > 0
  const codeValid = code.trim().length > 0
  const passwordValid = password.length > 0
  const formValid = loginValid && codeValid && passwordValid

  function handleSubmit(e) {
    e.preventDefault()
    setTouched({ login: true, code: true, password: true })

    if (!formValid) return

    setServerError('')
    // TODO: отправка на AUTH-002 (backend ещё не реализован)
    setServerError(t('loginWork.serverNotReady'))
  }

  function handleSendCode(e) {
    e.preventDefault()
    // TODO: отправка одноразового кода на бэкенде
  }

  return (
    <div className="loginwork-page">
      <div className="loginwork-card">
        <span className="loginwork-card__logo">{t('loginWork.logo')}</span>

        <form className="loginwork-form" onSubmit={handleSubmit} noValidate>
          <div className="loginwork-field">
            <label className="loginwork-field__label" htmlFor="login">
              {t('loginWork.login')}
            </label>
            <input
              className={`loginwork-field__input${touched.login && !loginValid ? ' loginwork-field__input--error' : ''}`}
              type="text"
              id="login"
              name="login"
              placeholder={t('loginWork.loginPlaceholder')}
              required
              value={login}
              onChange={(e) => setLogin(e.target.value)}
              onBlur={() => setTouched((prev) => ({ ...prev, login: true }))}
            />
            {touched.login && !loginValid && (
              <span className="loginwork-field__error">{t('loginWork.required')}</span>
            )}
          </div>

          <div className="loginwork-field">
            <label className="loginwork-field__label" htmlFor="code">
              {t('loginWork.code')}
            </label>
            <input
              className={`loginwork-field__input${touched.code && !codeValid ? ' loginwork-field__input--error' : ''}`}
              type="text"
              id="code"
              name="code"
              placeholder={t('loginWork.codePlaceholder')}
              maxLength="6"
              required
              value={code}
              onChange={(e) => setCode(e.target.value)}
              onBlur={() => setTouched((prev) => ({ ...prev, code: true }))}
            />
            {touched.code && !codeValid && (
              <span className="loginwork-field__error">{t('loginWork.required')}</span>
            )}
            <button
              className="loginwork-field__sublink"
              type="button"
              onClick={handleSendCode}
            >
              {t('loginWork.sendCode')}
            </button>
          </div>

          <div className="loginwork-field">
            <label className="loginwork-field__label" htmlFor="password">
              {t('loginWork.password')}
            </label>
            <div className="loginwork-field__wrap">
              <input
                className={`loginwork-field__input loginwork-field__input--password${touched.password && !passwordValid ? ' loginwork-field__input--error' : ''}`}
                type={passwordVisible ? 'text' : 'password'}
                id="password"
                name="password"
                placeholder={t('loginWork.passwordPlaceholder')}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onBlur={() => setTouched((prev) => ({ ...prev, password: true }))}
              />
              <button
                className={`loginwork-field__toggle${passwordVisible ? ' loginwork-field__toggle--visible' : ''}`}
                type="button"
                aria-label={passwordVisible ? t('loginWork.hidePassword') : t('loginWork.showPassword')}
                onClick={() => setPasswordVisible((v) => !v)}
              >
                <svg className="loginwork-field__eye loginwork-field__eye--open" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                <svg className="loginwork-field__eye loginwork-field__eye--closed" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
              </button>
            </div>
            {touched.password && !passwordValid && (
              <span className="loginwork-field__error">{t('loginWork.required')}</span>
            )}
            <Link className="loginwork-field__sublink" to="/forgot">
              {t('loginWork.forgotPassword')}
            </Link>
          </div>

          <button className="loginwork-form__submit" type="submit" disabled={!formValid}>
            {t('loginWork.submit')}
          </button>
        </form>

        {serverError && (
          <p className="loginwork-field__error" style={{ marginTop: 12 }}>
            {serverError}
          </p>
        )}

        <div className="loginwork-card__links">
          <p className="loginwork-card__no-account">
            {t('loginWork.noAccount')}{' '}
            <Link className="loginwork-card__link" to="/registration">
              {t('loginWork.registerLink')}
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
