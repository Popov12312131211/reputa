import { createContext, useContext, useEffect, useState } from 'react'

export const ROLES = {
  USER: 'user',
  EMPLOYEE: 'employee',
}

// Домашний маршрут для каждой роли: используется и route guard'ом RequireAuth,
// и страницами входа для редиректа после успешной аутентификации.
export const ROLE_HOME = {
  [ROLES.USER]: '/user/my',
  [ROLES.EMPLOYEE]: '/employee/settings',
}

const AuthContext = createContext(null)

// Сессия восстанавливается через GET /api/auth/me: бэкенд читает JWT из
// httpOnly-cookie (AUTH-007), фронтенд хранит только данные пользователя.
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    fetch('/api/auth/me', { credentials: 'include' })
      .then((res) => {
        if (!res.ok) throw new Error('unauthorized')
        return res.json()
      })
      .then((data) => {
        if (!cancelled) {
          setUser(data)
          setLoading(false)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setUser(null)
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  const role = user && user.role ? user.role : null

  // Сброс локального состояния сессии после выхода или удаления аккаунта.
  // Фактическое разлогинивание cookie выполняет бэкенд (/auth/logout,
  // /auth/delete) — здесь только очищаем данные пользователя на фронте.
  const clearSession = () => setUser(null)

  return (
    <AuthContext.Provider value={{ user, role, loading, setUser, clearSession }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return ctx
}