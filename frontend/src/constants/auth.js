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
