# Роли пользователей
ROLE_USER = "user"
ROLE_EMPLOYEE = "employee"
ROLE_MAX_LENGTH = 20

# Лимиты полей
FULL_NAME_MAX_LENGTH = 255
LOGIN_MAX_LENGTH = 255
PHONE_MAX_LENGTH = 20
TELEGRAM_MAX_LENGTH = 255
PASSWORD_HASH_MAX_LENGTH = 255

# Валидация пароля
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 64
PASSWORD_REGEX_UPPERCASE = r"[A-Z]"
PASSWORD_REGEX_LOWERCASE = r"[a-z]"
PASSWORD_REGEX_DIGIT = r"\d"
PASSWORD_REGEX_SPECIAL = r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?`~]"

# Статусы заявки
APPLICATION_STATUS_IN_QUEUE = "in_queue"
APPLICATION_STATUS_AUTO_APPROVED = "auto_approved"
APPLICATION_STATUS_AUTO_REJECTED = "auto_rejected"
APPLICATION_STATUS_EMPLOYEE_APPROVED = "employee_approved"
APPLICATION_STATUS_EMPLOYEE_REJECTED = "employee_rejected"
APPLICATION_STATUS_MAX_LENGTH = 32

# Лимиты полей заявки
AMOUNT_PRECISION = 12
AMOUNT_SCALE = 2
PURPOSE_MAX_LENGTH = 1024
TELEGRAM_CHANNEL_MAX_LENGTH = 255

# Оценка скоринга (0–100)
SCORE_MIN = 0
SCORE_MAX = 100

# Психологический портрет (метрики 0–10)
PORTRAIT_METRIC_MIN = 0
PORTRAIT_METRIC_MAX = 10

# Телефон: количество цифр без учёта ведущего '+'
PHONE_MIN_DIGITS = 7
PHONE_MAX_DIGITS = 15
# Паттерн собирается из лимитов выше, чтобы не дублировать 7/15 в двух местах
PHONE_PATTERN = rf"^\+?\d{{{PHONE_MIN_DIGITS},{PHONE_MAX_DIGITS}}}$"

# Префикс telegram-ника
TELEGRAM_PREFIX = "@"

# Хеширование пароля
PWD_SCHEME_BCRYPT = "bcrypt"

# Валидация даты рождения: отсев будущих дат и нереалистичного возраста
USER_MAX_AGE_YEARS = 150

# Сообщения API (общие для роутера, чтобы не дублировать строки)
MSG_USER_ALREADY_EXISTS = "Пользователь с таким логином уже существует"
