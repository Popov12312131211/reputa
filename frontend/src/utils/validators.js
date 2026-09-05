import { PHONE } from '../constants/auth'

// Общие валидаторы/форматтеры полей профиля, переиспользуемые страницами
// регистрации (Registration.jsx) и настроек (UserSettings.jsx), чтобы не
// дублировать одну и ту же логику в двух местах.

export function requiredIsValid(value) {
  return value.trim().length > 0
}

export function phoneIsValid(value) {
  return value.replace(/\D/g, '').length === PHONE.DIGITS
}

// Маска +7(XXX)XXX-XX-XX: 8 заменяется на 7 в начале, без «+» лишние цифры
// добавляются автоматически, максимум PHONE.DIGITS цифр.
export function formatPhone(digits) {
  let d = digits.replace(/\D/g, '')
  if (d.length > 0 && d[0] === '8') d = '7' + d.slice(1)
  if (d.length > 0 && d[0] !== '7') d = '7' + d
  d = d.slice(0, 11)

  let formatted = '+7'
  if (d.length > 1) formatted += '(' + d.slice(1, 4)
  if (d.length >= 4) formatted += ')'
  if (d.length > 4) formatted += d.slice(4, 7)
  if (d.length > 7) formatted += '-' + d.slice(7, 9)
  if (d.length > 9) formatted += '-' + d.slice(9, 11)
  return formatted
}