import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { registerSessionExpiredHandler } from '../api'

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

  // Текущая роль нужна обработчику «принудительной сессии», чтобы решить, на
  // какой экран входа уводить (сотрудник — /loginWork, обычный — /login).
  // Храним в ref, чтобы замыкание всегда видело актуальную роль без
  // перерегистрации обработчика на каждый рендер.
  const roleRef = useRef(null)
  const clearSession = useCallback(() => {
    roleRef.current = null
    setUser(null)
  }, [])
  const role = user && user.role ? user.role : null
  roleRef.current = role

  useEffect(() => {
    // AUTH-009: при истечении/невалидности JWT посреди работы приложение
    // принудительно разлогинивает пользователя и уводит на экран входа.
    // Сброс локальной сессии + жёсткий редирект (перезагружает страницу на
    // /login|/loginWork под свежий cookie) — надёжнее мягкого navigate, т.к.
    // AuthProvider живёт вне RouterProvider.
    registerSessionExpiredHandler(() => {
      const wasEmployee = roleRef.current === ROLES.EMPLOYEE
      clearSession()
      window.location.assign(wasEmployee ? '/loginWork' : '/login')
    })
  }, [clearSession])

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