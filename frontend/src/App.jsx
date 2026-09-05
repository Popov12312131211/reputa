import { Routes, Route } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import PlaceholderPage from './components/PlaceholderPage'
import Landing from './components/Landing'
import Login from './components/Login'
import LoginWork from './components/LoginWork'
import Registration from './components/Registration'
import UserNew from './components/UserNew'
import UserMy from './components/UserMy'
import EmployeeSettings from './components/EmployeeSettings'
import RequireAuth from './components/RequireAuth'
import { AuthProvider } from './contexts/AuthContext'

export default function App() {
  const { t } = useTranslation()

  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/registration" element={<Registration />} />
        <Route path="/loginWork" element={<LoginWork />} />
        <Route element={<RequireAuth />}>
          <Route path="/user/settings" element={<PlaceholderPage title={t('routes.userSettings')} />} />
          <Route path="/user/my" element={<UserMy />} />
          <Route path="/user/new" element={<UserNew />} />
          <Route path="/employee/settings" element={<EmployeeSettings />} />
          <Route path="/employee/newApplication" element={<PlaceholderPage title={t('routes.employeeNewApplication')} />} />
          <Route path="/employee/application" element={<PlaceholderPage title={t('routes.employeeApplication')} />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}
