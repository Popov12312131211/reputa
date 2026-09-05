import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { Paperclip } from 'lucide-react'
import { postFormData } from '../api'
import { TELEGRAM } from '../constants/auth'
import { AMOUNT } from '../constants/application'
import './UserNew.css'

const REASON_PLACEHOLDER_KEYS = [
  'userNew.reasonPlaceholder1',
  'userNew.reasonPlaceholder2',
  'userNew.reasonPlaceholder3',
  'userNew.reasonPlaceholder4',
  'userNew.reasonPlaceholder5',
  'userNew.reasonPlaceholder6',
  'userNew.reasonPlaceholder7',
]

export default function UserNew() {
  const { t } = useTranslation()
  const navigate = useNavigate()

  const [amount, setAmount] = useState('')
  const [reason, setReason] = useState('')
  const [telegram, setTelegram] = useState('')
  const [channel, setChannel] = useState('')
  const [file, setFile] = useState(null)
  const [password, setPassword] = useState('')
  const [passwordVisible, setPasswordVisible] = useState(false)
  const [consent, setConsent] = useState(false)
  const [touched, setTouched] = useState({})
  const [serverError, setServerError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  // Плейсхолдер выбирается один раз при монтировании (не меняется при ре-рендерах);
  // обновляется только при новой загрузке страницы.
  const [reasonPlaceholder] = useState(() => {
    const index = Math.floor(Math.random() * REASON_PLACEHOLDER_KEYS.length)
    return t(REASON_PLACEHOLDER_KEYS[index])
  })

  const amountNum = Number(amount)
  const amountValid =
    amount.trim() !== '' &&
    Number.isFinite(amountNum) &&
    amountNum >= AMOUNT.MIN &&
    amountNum <= AMOUNT.MAX
  const telegramValid = telegram.trim() === '' || TELEGRAM.isValid(telegram)
  const channelValid = channel.trim() === '' || TELEGRAM.isValid(channel)
  const reasonValid = reason.trim() !== ''
  const fileValid = file != null
  const passwordValid = password.length > 0
  const formValid = amountValid && telegramValid && channelValid && reasonValid && fileValid && passwordValid && consent

  async function handleSubmit(e) {
    e.preventDefault()
    setTouched({ amount: true, reason: true, telegram: true, channel: true, password: true, statement: true })

    if (!formValid || submitting) return

    setServerError('')
    setSubmitting(true)

    // APP-002: multipart-форма POST /api/applications (amount, purpose, telegram,
    // telegram_channel, statement). Поле пароля остаётся клиентской проверкой —
    // backend-эндпоинт его не принимает.
    const formData = new FormData()
    formData.append('amount', amount)
    formData.append('purpose', reason)
    formData.append('telegram', telegram)
    formData.append('telegram_channel', channel)
    if (file) formData.append('statement', file)

    const res = await postFormData('/api/applications', formData)
    setSubmitting(false)

    if (res.ok) {
      navigate('/user/my')
      return
    }
    setServerError(res.error || t('userNew.submitError'))
  }

  return (
    <div className="usernew-page">
      <div className="usernew-page__inner">
        <h1 className="usernew-page__title">{t('userNew.title')}</h1>

        <div className="usernew-card">
          <form className="usernew-form" onSubmit={handleSubmit} noValidate>
            <div className="usernew-field">
              <label className="usernew-field__label" htmlFor="amount">
                {t('userNew.amount')}
              </label>
              <input
                className={`usernew-field__input${touched.amount && !amountValid ? ' usernew-field__input--error' : ''}`}
                type="number"
                id="amount"
                name="amount"
                inputMode="decimal"
                min={AMOUNT.MIN}
                max={AMOUNT.MAX}
                step="1000"
                required
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                onBlur={() => setTouched((prev) => ({ ...prev, amount: true }))}
              />
              {touched.amount && !amountValid && (
                <span className="usernew-field__error">{t('userNew.amountHint')}</span>
              )}
            </div>

            <div className="usernew-field">
              <label className="usernew-field__label" htmlFor="reason">
                {t('userNew.reason')}
              </label>
              <textarea
                className={`usernew-field__textarea${touched.reason && !reasonValid ? ' usernew-field__textarea--error' : ''}`}
                id="reason"
                name="reason"
                rows="4"
                placeholder={reasonPlaceholder}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
              {touched.reason && !reasonValid && (
                <span className="usernew-field__error">{t('userNew.required')}</span>
              )}
            </div>

            <div className="usernew-row">
              <div className="usernew-field">
                <label className="usernew-field__label" htmlFor="telegram">
                  {t('userNew.telegram')}
                </label>
                <input
                  className={`usernew-field__input${touched.telegram && !telegramValid ? ' usernew-field__input--error' : ''}`}
                  type="text"
                  id="telegram"
                  name="telegram"
                  placeholder={t('userNew.telegramPlaceholder')}
                  value={telegram}
                  onChange={(e) => setTelegram(TELEGRAM.format(e.target.value))}
                  onFocus={() => {
                    if (!telegram) setTelegram('@')
                  }}
                  onBlur={() => {
                    if (telegram === '@') setTelegram('')
                    setTouched((prev) => ({ ...prev, telegram: true }))
                  }}
                />
                {touched.telegram && !telegramValid && (
                  <span className="usernew-field__error">{t('userNew.telegramHint')}</span>
                )}
              </div>

              <div className="usernew-field">
                <label className="usernew-field__label" htmlFor="channel">
                  {t('userNew.channel')}
                </label>
                <input
                  className={`usernew-field__input${touched.channel && !channelValid ? ' usernew-field__input--error' : ''}`}
                  type="text"
                  id="channel"
                  name="channel"
                  placeholder={t('userNew.channelPlaceholder')}
                  value={channel}
                  onChange={(e) => setChannel(TELEGRAM.format(e.target.value))}
                  onFocus={() => {
                    if (!channel) setChannel('@')
                  }}
                  onBlur={() => {
                    if (channel === '@') setChannel('')
                    setTouched((prev) => ({ ...prev, channel: true }))
                  }}
                />
                {touched.channel && !channelValid && (
                  <span className="usernew-field__error">{t('userNew.channelHint')}</span>
                )}
              </div>
            </div>

            <div className="usernew-field">
              <label className="usernew-field__label" htmlFor="statement">
                {t('userNew.statement')}
              </label>
              <label className={`usernew-file${file ? ' usernew-file--filled' : ''}`} htmlFor="statement">
                <input
                  className="usernew-file__input"
                  type="file"
                  id="statement"
                  name="statement"
                  onChange={(e) =>
                    setFile(e.target.files && e.target.files.length > 0 ? e.target.files[0] : null)
                  }
                />
                <span className="usernew-file__name">
                  {file ? file.name : t('userNew.statementPlaceholder')}
                </span>
                <Paperclip className="usernew-file__icon" size={20} strokeWidth={1.5} />
              </label>
              {touched.statement && !fileValid && (
                <span className="usernew-field__error">{t('userNew.required')}</span>
              )}
            </div>

            <label className="usernew-checkbox">
              <input
                className="usernew-checkbox__input"
                type="checkbox"
                checked={consent}
                onChange={(e) => setConsent(e.target.checked)}
              />
              <span className="usernew-checkbox__text">{t('userNew.consent')}</span>
            </label>

            <div className="usernew-actions">
              <div className="usernew-field">
                <label className="usernew-field__label" htmlFor="password">
                  {t('userNew.password')}
                </label>
                <div className="usernew-field__wrap">
                  <input
                    className={`usernew-field__input usernew-field__input--password${touched.password && !passwordValid ? ' usernew-field__input--error' : ''}`}
                    type={passwordVisible ? 'text' : 'password'}
                    id="password"
                    name="password"
                    placeholder={t('userNew.passwordPlaceholder')}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onBlur={() => setTouched((prev) => ({ ...prev, password: true }))}
                  />
                  <button
                    className={`usernew-field__toggle${passwordVisible ? ' usernew-field__toggle--visible' : ''}`}
                    type="button"
                    aria-label={passwordVisible ? t('userNew.hidePassword') : t('userNew.showPassword')}
                    onClick={() => setPasswordVisible((v) => !v)}
                  >
                    <svg className="usernew-field__eye usernew-field__eye--open" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                    <svg className="usernew-field__eye usernew-field__eye--closed" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                  </button>
                </div>
                {touched.password && !passwordValid && (
                  <span className="usernew-field__error">{t('userNew.required')}</span>
                )}
              </div>

              <button className="usernew-form__submit" type="submit" disabled={!formValid || submitting}>
                {t('userNew.submit')}
              </button>
            </div>
          </form>

          {serverError && (
            <p className="usernew-field__error" style={{ marginTop: 12 }}>
              {serverError}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}