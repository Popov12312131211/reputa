// Общий helper для POST-запросов к API. Все запросы идут на относительный
// /api/...: в dev-режиме проксирует Vite, в проде — nginx, и оба срезают
// префикс /api перед передачей на бэкенд.
export async function getJSON(url) {
  const res = await fetch(url, { credentials: 'include' })

  let data = null
  try {
    data = await res.json()
  } catch {
    // не-JSON ответ
  }

  if (!res.ok) {
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
    return { ok: false, error: extractError(data) }
  }
  return { ok: true, data }
}