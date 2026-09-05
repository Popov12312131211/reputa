import { Navigate, useLocation } from 'react-router-dom'
import { useAuth, ROLES } from '../contexts/AuthContext'
import Layout from './Layout'

// Route guard для приватных маршрутов (/user/*, /employee/*):
// гости пользовательской зоны уходят на /login, гости зоны сотрудников —
// на /loginWork; пользователя с чужой ролью перенаправляем в его кабинет.
const ROLE_HOME = {
  [ROLES.USER]: '/user/my',
  [ROLES.EMPLOYEE]: '/employee/settings',
}

export default function RequireAuth() {
  const { user, role, loading } = useAuth()
  const { pathname } = useLocation()

  if (loading) return null

  const isEmployeeArea = pathname === '/employee' || pathname.startsWith('/employee/')
  if (!user) {
    return <Navigate to={isEmployeeArea ? '/loginWork' : '/login'} replace />
  }

  // Неизвестная роль не должна циклично возвращать пользователя на тот же маршрут.
  const home = ROLE_HOME[role]
  if (!home) return <Navigate to="/login" replace />

  const expectedRole = isEmployeeArea ? ROLES.EMPLOYEE : ROLES.USER
  if (role !== expectedRole) {
    return <Navigate to={home} replace />
  }

  return <Layout />
}