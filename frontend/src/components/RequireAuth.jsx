import { Navigate, useLocation } from 'react-router-dom'
import { useAuth, ROLES } from '../contexts/AuthContext'
import Layout from './Layout'

// Route guard для приватных маршрутов (/user/*, /employee/*):
// неавторизованный пользователь уходит на /login, пользователя с чужой ролью
// перенаправляем в его кабинет.
export default function RequireAuth() {
  const { user, role, loading } = useAuth()
  const { pathname } = useLocation()

  if (loading) return null

  if (!user) return <Navigate to="/login" replace />

  const isEmployeeArea = pathname.startsWith('/employee')
  const expectedRole = isEmployeeArea ? ROLES.EMPLOYEE : ROLES.USER
  if (role !== expectedRole) {
    const home = role === ROLES.EMPLOYEE ? '/employee/settings' : '/user/my'
    return <Navigate to={home} replace />
  }

  return <Layout />
}