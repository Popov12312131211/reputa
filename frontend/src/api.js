// Общий helper для POST-запросов к API. Все запросы идут на относительный
// /api/...: в dev-режиме проксирует Vite, в проде — nginx, и оба срезают
// префикс /api перед передачей на бэкенд.

// --- Принудительная сессия (AUTH-009) ---
// JWT в httpOnly-cookie может протухнуть посреди работы. Любой API-запрос,
// вернувший 401 на защищённом маршруте, означает, что сессия больше не
// валидна: фронт должен принудительно разлогинить пользователя и увести на
// /login (а не просто показать ошибку в компоненте).
//
// Храним ссылку на обработчик, который регистрирует AuthProvider (он знает,
// как сбросить состояние сессии и куда перенаправить). Эндпоинты входа/поиска
// аккаунта возвращают 401 и по «обычным» причинам (неверный логин/пароль/код,
// аккаунта нет), поэтому они исключены — иначе логин-страница вечно бы
// перезагружалась.

const AUTH_EXEMPT_PATHS = new Set([
  '/api/auth/login',
  '/api/auth/login/employee',
  '/api/auth/register',
  '/api/auth/register/employee',
])

let sessionExpiredHandler = null

export function registerSessionExpiredHandler(handler) {
  sessionExpiredHandler = handler
}

function handleUntrustedAuth(url, res) {
  if (res.status === 401 && !AUTH_EXEMPT_PATHS.has(url) && sessionExpiredHandler) {
    sessionExpiredHandler()
  }
}

export async function getJSON(url) {
  const res = await fetch(url, { credentials: 'include' })

  let data = null
  try {
    data = await res.json()
  } catch {
    // не-JSON ответ
  }

  if (!res.ok) {
    handleUntrustedAuth(url, res)
    const detail = data && typeof data.detail === 'string' ? data.detail : null
    return { ok: false, error: detail }
  }
  return { ok: true, data }
}

export async function postJSON(url, body) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(body),
  })

  let data = null
  try {
    data = await res.json()
  } catch {
    // не-JSON ответ — расцениваем как обычную сетевую ошибку ниже
  }

  if (!res.ok) {
    handleUntrustedAuth(url, res)
    // Быстрый код обычно приходит один строкой в detail (401/403/409),
    // ошибки валидации (422) — массивом объектов, для них отдельного текста нет.
    const detail = data && typeof data.detail === 'string' ? data.detail : null
    return { ok: false, error: detail }
  }
  return { ok: true, data }
}

// POST с multipart/form-data (загрузка файлов). Content-Type не задаём —
// браузер сам выставляет его вместе с случайной boundary.
export async function postFormData(url, formData) {
  const res = await fetch(url, {
    method: 'POST',
    credentials: 'include',
    body: formData,
  })

  let data = null
  try {
    data = await res.json()
  } catch {
    // не-JSON ответ — расцениваем как обычную сетевую ошибку ниже
  }

  if (!res.ok) {
    handleUntrustedAuth(url, res)
    const detail = data && typeof data.detail === 'string' ? data.detail : null
    return { ok: false, error: detail }
  }
  return { ok: true, data }
}

// Извлекает текст ошибки из ответа: быстрые коды приходят строкой в detail
// (401/403/409), ошибки валидации (422) — массивом объектов с полем msg,
// их склеиваем в одну строку для показа.
function extractError(data) {
  const detail = data && data.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const msgs = detail
      .map((item) => {
        const msg = item && typeof item.msg === 'string' ? item.msg : ''
        return msg.replace(/^Value error,\s*/, '')
      })
      .filter(Boolean)
    return msgs.length > 0 ? msgs.join('; ') : null
  }
  return null
}

export async function putJSON(url, body) {
  const res = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(body),
  })
  let data = null
  try {
    data = await res.json()
  } catch {
    // не-JSON ответ — расцениваем как обычную сетевую ошибку ниже
  }

  if (!res.ok) {
    handleUntrustedAuth(url, res)
    return { ok: false, error: extractError(data) }
  }
  return { ok: true, data }
}

// PATCH-запрос (напр. обновление профиля). Логика та же, что у putJSON.
export async function patchJSON(url, body) {
  const res = await fetch(url, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(body),
  })

  let data = null
  try {
    data = await res.json()
  } catch {
    // не-JSON ответ — расцениваем как обычную сетевую ошибку ниже
  }

  if (!res.ok) {
    handleUntrustedAuth(url, res)
    return { ok: false, error: extractError(data) }
  }
  return { ok: true, data }
}

// DELETE-запрос (напр. удаление аккаунта). Успех 204 идёт без тела — data=null,
// поэтому контракт тот же: { ok: true, data } / { ok: false, error }.
export async function deleteJSON(url) {
  const res = await fetch(url, {
    method: 'DELETE',
    credentials: 'include',
  })

  let data = null
  try {
    data = await res.json()
  } catch {
    // 204/не-JSON ответ
  }

  if (!res.ok) {
    handleUntrustedAuth(url, res)
    return { ok: false, error: extractError(data) }
  }
  return { ok: true, data }
}