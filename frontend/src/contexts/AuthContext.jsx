import { createContext, useContext } from 'react'
import { useLocation } from 'react-router-dom'

export const ROLES = {
  USER: 'user',
  EMPLOYEE: 'employee',
}

const AuthContext = createContext(null)

// Роль определяется из текущего URL-пути: /user/* -> user, /employee/* -> employee.
// Когда бэкендная аутентификация (JWT) будет реализована — провайдер обновляется
// для чтения роли из токена/API, компоненты-потребители при этом не меняются.
export function AuthProvider({ children }) {
  const { pathname } = useLocation()

  const role = pathname.startsWith('/employee') ? ROLES.EMPLOYEE : ROLES.USER

  return <AuthContext.Provider value={{ role }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}
