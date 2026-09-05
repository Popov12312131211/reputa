export const SHOW_AUTH_ILLUSTRATION = true

export const PASSWORD = {
  MIN_LENGTH: 8,
  MAX_LENGTH: 64,
}

export const PHONE = {
  DIGITS: 11,
}

export const DATE = {
  MIN_YEAR: 1900,
  MIN_AGE: 18,
}

export const PASSWORD_RULES = [
  { key: 'length', test: (v) => v.length >= PASSWORD.MIN_LENGTH && v.length <= PASSWORD.MAX_LENGTH },
  { key: 'case', test: (v) => /[a-z]/.test(v) && /[A-Z]/.test(v) },
  { key: 'digit', test: (v) => /\d/.test(v) },
  { key: 'special', test: (v) => /[!@#$_]/.test(v) },
]

export const PHONE_MASK = '+7(XXX)XXX-XX-XX'

export const TELEGRAM = {
  isValid: (value) => /^@[A-Za-z0-9_]+$/.test(value.trim()),
  format: (value) => {
    let v = value
    while (v.indexOf('@@') === 0) v = v.slice(1)
    if (v.length > 0 && v[0] !== '@') v = '@' + v
    return v
  },
}
