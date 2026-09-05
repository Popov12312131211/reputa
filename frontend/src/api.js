// Общий helper для POST-запросов к API. Все запросы идут на относительный
// /api/...: в dev-режиме проксирует Vite, в проде — nginx, и оба срезают
// префикс /api перед передачей на бэкенд.
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