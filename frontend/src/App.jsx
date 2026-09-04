import { Routes, Route } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import PlaceholderPage from './components/PlaceholderPage'

export default function App() {
  const { t } = useTranslation()

  return (
    <Routes>
      <Route path="/" element={<PlaceholderPage title={t('routes.home')} />} />
      <Route path="/login" element={<PlaceholderPage title={t('routes.login')} />} />
      <Route path="/registration" element={<PlaceholderPage title={t('routes.registration')} />} />
      <Route path="/loginWork" element={<PlaceholderPage title={t('routes.loginWork')} />} />
      <Route path="/user/settings" element={<PlaceholderPage title={t('routes.userSettings')} />} />
      <Route path="/user/my" element={<PlaceholderPage title={t('routes.userMy')} />} />
      <Route path="/user/new" element={<PlaceholderPage title={t('routes.userNew')} />} />
      <Route path="/employee/settings" element={<PlaceholderPage title={t('routes.employeeSettings')} />} />
      <Route path="/employee/newApplication" element={<PlaceholderPage title={t('routes.employeeNewApplication')} />} />
      <Route path="/employee/application" element={<PlaceholderPage title={t('routes.employeeApplication')} />} />
    </Routes>
  )
}
