import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import './UserSettings.css'

const initialValues = {
  full_name: '',
  login: '',
  telegram: '',
  phone: '',
  password: '',
}

export default function UserSettings() {
  const { t } = useTranslation()
  const [values, setValues] = useState(initialValues)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })

  useEffect(() => {
    async function loadProfile() {
      try {
        const response = await fetch('/auth/profile', { credentials: 'include' })
        if (!response.ok) throw new Error('profile-load')
        const profile = await response.json()
        setValues({ ...initialValues, ...profile, password: '' })
      } catch {
        setMessage({ type: 'error', text: t('userSettings.loadError') })
      } finally {
        setLoading(false)
      }
    }

    loadProfile()
  }, [t])

  function setField(field, value) {
    setValues((current) => ({ ...current, [field]: value }))
    setMessage({ type: '', text: '' })
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setSaving(true)
    setMessage({ type: '', text: '' })

    try {
      const response = await fetch('/auth/profile', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(values),
      })
      const data = await response.json()
      if (!response.ok) {
        const saveError = Array.isArray(data.detail)
          ? data.detail[0]?.msg || data.detail
          : data.detail || t('userSettings.saveError')
        throw new Error(saveError)
      }
      setValues((current) => ({ ...current, ...data, password: '' }))
      setMessage({ type: 'success', text: t('userSettings.saved') })
    } catch (error) {
      setMessage({ type: 'error', text: error.message || t('userSettings.saveError') })
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div className="user-settings"><p className="user-settings__status">{t('userSettings.loading')}</p></div>
  }

  return (
    <section className="user-settings">
      <div className="user-settings__heading">
        <p className="user-settings__eyebrow">{t('userSettings.eyebrow')}</p>
        <h1>{t('userSettings.title')}</h1>
        <p className="user-settings__description">{t('userSettings.description')}</p>
      </div>

      <form className="user-settings__form" onSubmit={handleSubmit}>
        <div className="user-settings__fields">
          <label>
            <span>{t('userSettings.fullName')}</span>
            <input value={values.full_name} onChange={(event) => setField('full_name', event.target.value)} required />
          </label>
          <label>
            <span>{t('userSettings.login')}</span>
            <input value={values.login} onChange={(event) => setField('login', event.target.value)} required />
          </label>
          <label>
            <span>{t('userSettings.telegram')}</span>
            <input value={values.telegram} onChange={(event) => setField('telegram', event.target.value)} required />
          </label>
          <label>
            <span>{t('userSettings.phone')}</span>
            <input type="tel" value={values.phone} onChange={(event) => setField('phone', event.target.value)} required />
          </label>
          <label className="user-settings__password">
            <span>{t('userSettings.newPassword')}</span>
            <input type="password" value={values.password} onChange={(event) => setField('password', event.target.value)} placeholder={t('userSettings.passwordPlaceholder')} />
          </label>
        </div>

        {message.text && <p className={`user-settings__message user-settings__message--${message.type}`}>{message.text}</p>}
        <button className="user-settings__submit" type="submit" disabled={saving}>
          {saving ? t('userSettings.saving') : t('userSettings.save')}
        </button>
      </form>
    </section>
  )
}