
import io
import re
from datetime import date, datetime
from decimal import Decimal

import pdfplumber

from app.core.constants import (
    STMT_CATEGORY_CAFES,
    STMT_CATEGORY_GROCERIES,
    STMT_CATEGORY_HEALTH,
    STMT_CATEGORY_INCOME,
    STMT_CATEGORY_OTHER,
    STMT_CATEGORY_SERVICES,
    STMT_CATEGORY_SHOPPING,
    STMT_CATEGORY_TRANSFERS,
    STMT_CATEGORY_TRANSPORT,
    STMT_CATEGORY_UTILITIES,
    STATEMENT_BANK_ALFA,
    STATEMENT_BANK_OZON,
    STATEMENT_BANK_SBER,
    STATEMENT_BANK_TBANK,
)
from app.schemas.statement import ParsedBankStatement, StatementTransaction

_DATE_RE = re.compile(r"\d{2}\.\d{2}\.\d{2,4}")

# Сумма с разделителем тысяч-пробелом, десятичной точкой/запятой и необязательным знаком.
_AMOUNT_RE = r"[+-]?\d{1,3}(?:[ \u00A0]\d{3})*[.,]\d{2}"

# Разновидность суммы без знака (колонка «Сумма» Альфа-Банка и остатки).
_UNSIGNED_AMOUNT_RE = r"-?\s*\d{1,3}(?:[ \u00A0]\d{3})*[.,]\d{2}"

# Альфа-Банк: сумма в конце строки, перед токеном RUR (отрицательная — с минусом).
_ALFA_AMOUNT_END_RE = re.compile(rf"({_UNSIGNED_AMOUNT_RE})\s+RUR\s*$")


# СберБанк, первая строка операции: дата, время, категория, сумма, остаток.
# Категория «ленивая»: движок откатывается так, чтобы последними шли два числа.
_SBER_TX_RE = re.compile(
    rf"^(\d{{2}}\.\d{{2}}\.\d{{4}}) (\d{{2}}:\d{{2}}) (.+?)({_AMOUNT_RE}) ({_AMOUNT_RE})$"
)
# СберБанк, вторая строка операции: дата обработки + 6-значный код авторизации.
_SBER_PROC_RE = re.compile(r"^(\d{2}\.\d{2}\.\d{4}) (\d{6}) (.+)$")

_ALFA_TX_START_RE = re.compile(r"^(\d{2}\.\d{2}\.\d{4})\s+(\S+)\s*(.*)$")
_ALFA_HOLD_START_RE = re.compile(r"^HOLD\s+(.*)$")
_ALFA_MCC_RE = re.compile(r"MCC(\d{4})", re.IGNORECASE)

# Сумма в шапке Альфа-Банка: входящий/исходящий остаток, поступления, расходы.
_ALFA_HEADER_AMOUNT_RE = re.compile(rf"({_UNSIGNED_AMOUNT_RE})\s+RUR")

# Сумма в таблице Озон-Банка: необязательный знак, пробелы-разделители тысяч,
# десятичная точка, валюта ₽ на конце.
_OZON_AMOUNT_RE = re.compile(r"^\s*[+-]?\s*[\d\s.,]+\s*₽?\s*$")

# Шум, который pdfplumber оставляет между операциями на стыках страниц.
_ALFA_NOISE_SUBSTRINGS = (
    "Дата проводки",
    "в валюте счета",
    "Уполномоченное лицо",
    "подпись сотрудника",
    "Ф.И.О. сотрудника",
    "Страница",
    "А.А. Панченко",
)
_SBER_NOISE_SUBSTRINGS = (
    "Страница",
    "Продолжение на следующей странице",
    "Дата формирования документа",
    "Выписка по счёту дебетовой карты",
)

# Категории по ключевым словам в описании. Порядок важен: более специфичные
# категории идут раньше «переводов», чтобы покупка не попала в переводы.
_KEYWORD_CATEGORIES = (
    (
        STMT_CATEGORY_GROCERIES,
        (
            "магнит", "пятерочка", "пятёрочка", "перекресток", "перекрёсток",
            "ашан", "вкусвилл", "спар", "дикси", "продукт", "market", "magnit",
            "pyaterochka", "универсам", "супермаркет", "карусель", "yarche", "ярче",
            "krasnoe&beloe", "к&б", "лента", "lenta", "monetka", "монетка", "fixprice",
        ),
    ),
    (
        STMT_CATEGORY_CAFES,
        (
            "кафе", "ресторан", "кофе", "кебаб", "шаурма", "пицца", "бургер",
            "вкусно и точка", "kebab", "coffee", "kofetochka", "столовая",
            "свежар", "svezhar", "жар с", "rostics", "shashlykoff", "dobropek",
        ),
    ),
    (
        STMT_CATEGORY_TRANSPORT,
        (
            "метро", "метрополитен", "автобус", "такси", "транспорт",
            "metroelectrotrans", "transkart", "трамвай", "билет", "аэрофлот",
            "сапсан", "каршеринг", "уехать",
        ),
    ),
    (
        STMT_CATEGORY_HEALTH,
        ("аптека", "лекарств", "клиник", "больниц", "доктор", "медицин", "apteka", "здоровь"),
    ),
    (
        STMT_CATEGORY_UTILITIES,
        (
            "жкх", "жилком", "электроэнерг", "коммунальн", "интернет", "связь",
            "телеком", "ростелеком", "мегафон", "мтс", "билайн", "телефон",
            "rostelecom", "водоканал",
        ),
    ),
    (
        STMT_CATEGORY_SERVICES,
        (
            "подписк", "getcourse", "яндекс плюс", "кино", "музык", "облако",
            "образован", "урок", "курс",
        ),
    ),
    (
        STMT_CATEGORY_SHOPPING,
        (
            "ozon", "wildberries", "маркетплейс", "алиэкспресс", "аппарат",
            "техник", "одежд", "обувь", "магазин", "заказ", "золотое яблоко",
            "реклама",
        ),
    ),
    (
        STMT_CATEGORY_TRANSFERS,
        ("перевод", "платеж", "платёж", "сбп", "sbp", "cashback", "выплата", "возврат", "оплата"),
    ),
)


class StatementParseError(Exception):
    """Содержимое файла не удалось разобрать ни одним из известных форматов."""


class UnsupportedStatementError(StatementParseError):
    """Файл не распознан как выписка ни одного из поддерживаемых банков."""


def _parse_date(value: str) -> date:
    fmt = "%d.%m.%Y" if len(value.split(".")[-1]) == 4 else "%d.%m.%y"
    return datetime.strptime(value, fmt).date()


def _parse_amount(text: str) -> Decimal:
    """'-1 234,56' -> Decimal('-1234.56'); '+' и пробелы отбрасываются."""
    cleaned = text.replace("\u00A0", " ").replace(" ", "")
    sign = -1 if "-" in cleaned else 1
    cleaned = cleaned.replace("+", "").replace("-", "")
    # Отбрасываем всё, кроме цифр и разделителей дробной части: валютные суффиксы
    # (₽, RUR, руб.) и прочие текстовые остатки в столбце суммы не числа.
    digits = re.sub(r"[^\d.,]", "", cleaned)
    return sign * Decimal(digits.replace(",", "."))


def _split_amount_from_end(line: str) -> tuple[str, Decimal | None]:
    """Отрезает сумму «N RUR» с конца строки, если она там есть."""
    m = _ALFA_AMOUNT_END_RE.search(line)
    if not m:
        return line, None
    return line[: m.start()].rstrip(), _parse_amount(m.group(1))


def _extract_lines(content: bytes) -> list[str]:
    if not content:
        raise StatementParseError("Файл выписки пуст")
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            lines: list[str] = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines.extend(text.splitlines())
    except Exception as exc:
        # pdfplumber бросает разнородные исключения на битых и не-PDF файлах —
        # любое из них превращаем в единую ошибку разбора.
        raise StatementParseError(f"Не удалось прочитать файл: {exc}") from exc
    if not lines:
        raise StatementParseError("В файле не найден текст")
    return lines


def _extract_tables(content: bytes) -> tuple[list[str], list]:
    try:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            text_lines = [line for page in pdf.pages for line in (page.extract_text() or "").splitlines()]
            tables = [row for page in pdf.pages for t in (page.extract_tables() or []) for row in t]
    except Exception as exc:
        raise StatementParseError(f"Не удалось прочитать файл: {exc}") from exc
    if not text_lines:
        raise StatementParseError("В файле не найден текст")
    return text_lines, tables


def _categorize(description: str, amount: Decimal, *, sber_category: str | None = None) -> str:
    if amount > 0:
        return STMT_CATEGORY_INCOME

    mcc = _ALFA_MCC_RE.search(description)
    if mcc:
        mcc_code = int(mcc.group(1))
        if mcc_code == 5411:
            return STMT_CATEGORY_GROCERIES
        if mcc_code in (5811, 5812, 5813, 5814):
            return STMT_CATEGORY_CAFES
        if mcc_code == 5912:
            return STMT_CATEGORY_HEALTH
        if mcc_code in (4111, 4121, 4131):
            return STMT_CATEGORY_TRANSPORT
        if mcc_code == 4816:
            return STMT_CATEGORY_UTILITIES
        if mcc_code == 7277:
            return STMT_CATEGORY_SERVICES

    lowered = description.lower()
    for category, keywords in _KEYWORD_CATEGORIES:
        if any(kw in lowered for kw in keywords):
            return category

    # У СберБанка категория операции приходит отдельной колонкой.
    if sber_category:
        return STMT_CATEGORY_TRANSFERS

    return STMT_CATEGORY_OTHER


def _summarize(transactions: list[StatementTransaction], bank: str) -> dict:
    income = Decimal(0)
    expenses = Decimal(0)
    by_category: dict[str, Decimal] = {}
    for tx in transactions:
        if tx.amount > 0:
            income += tx.amount
        else:
            expenses += -tx.amount
            by_category[tx.category] = by_category.get(tx.category, Decimal(0)) + (-tx.amount)
    return {"income": income, "expenses": expenses, "expenses_by_category": by_category}


def _parse_alfa(lines: list[str]) -> ParsedBankStatement:
    header_lines: list[str] = []
    rest: list[str] = []
    in_transactions = False
    for line in lines:
        if in_transactions:
            rest.append(line)
        else:
            header_lines.append(line)
            if "Операции по счету" in line:
                in_transactions = True

    joined_header = "\n".join(header_lines)

    period_m = re.search(r"За период с (\d{2}\.\d{2}\.\d{4}) по (\d{2}\.\d{2}\.\d{4})", joined_header)
    if not period_m:
        raise StatementParseError("В выписке Альфа-Банка не найден период")
    period_start, period_end = _parse_date(period_m.group(1)), _parse_date(period_m.group(2))

    account_m = re.search(r"Номер счета (\d{6,})", joined_header)
    opening_m = re.search(rf"Входящий остаток\s+({_UNSIGNED_AMOUNT_RE})\s+RUR", joined_header)
    closing_m = re.search(rf"Исходящий остаток\s+({_UNSIGNED_AMOUNT_RE})\s+RUR", joined_header)
    if not opening_m or not closing_m:
        raise StatementParseError("В выписке Альфа-Банка не найдены остатки")

    # Блок строк одной операции. Начало блока — строка с датой или HOLD (StmtMe),
    # всё остальное до следующего начала относится к описанию этой операции.
    raw_transactions: list[tuple[date, str, Decimal]] = []
    current_description: list[str] | None = None
    current_amount: Decimal | None = None
    current_date: date | None = None

    def flush_block() -> None:
        nonlocal current_description, current_amount
        if current_description is None or current_amount is None:
            return
        raw_transactions.append((current_date, " ".join(current_description).strip(), current_amount))
        current_description = None
        current_amount = None

    for line in rest:
        tx_start = _ALFA_TX_START_RE.match(line)
        hold_start = _ALFA_HOLD_START_RE.match(line) if not tx_start else None
        if tx_start:
            flush_block()
            current_date = _parse_date(tx_start.group(1))
            body, amount = _split_amount_from_end(line)
            current_amount = amount
            current_description = [body.strip()]
        elif hold_start:
            flush_block()
            body, amount = _split_amount_from_end(line)
            hold_date_m = re.search(r"дата операции:\s*(\d{2}\.\d{2}\.\d{4})", line)
            current_date = _parse_date(hold_date_m.group(1)) if hold_date_m else period_end
            current_amount = amount
            current_description = [body.strip()]
        elif current_description is not None:
            if any(noise in line for noise in _ALFA_NOISE_SUBSTRINGS):
                continue
            current_description.append(line.strip())
    flush_block()

    transactions = [
        StatementTransaction(
            date=tdate,
            description=description,
            amount=amount,
            category=_categorize(description, amount),
        )
        for tdate, description, amount in raw_transactions
    ]

    return ParsedBankStatement(
        bank=STATEMENT_BANK_ALFA,
        account_number=account_m.group(1) if account_m else None,
        period_start=period_start,
        period_end=period_end,
        opening_balance=_parse_amount(opening_m.group(1)),
        closing_balance=_parse_amount(closing_m.group(1)),
        transactions=transactions,
        **_summarize(transactions, STATEMENT_BANK_ALFA),
    )


def _parse_sber(lines: list[str]) -> ParsedBankStatement:
    header_lines: list[str] = []
    rest: list[str] = []
    for i, line in enumerate(lines):
        if "Расшифровка операций" in line:
            header_lines = lines[:i]
            rest = lines[i:]
            break

    joined_header = "\n".join(header_lines)

    # Период выписки — строка «За период 01.06.2026 — 01.09.2026»; другие даты
    # в шапке (дата открытия счёта и т.п.) не должны попадать в период.
    period_m = re.search(r"За период\s+(\d{2}\.\d{2}\.\d{4})\s*[—\-]\s*(\d{2}\.\d{2}\.\d{4})", joined_header.replace("—", "-"))
    if period_m:
        period_start, period_end = _parse_date(period_m.group(1)), _parse_date(period_m.group(2))
    else:
        period_start = period_end = None

    balances = re.findall(r"Остаток на \d{2}\.\d{2}\.\d{4}\s+([+-]?\s*\d{1,3}(?:[ \u00A0]\d{3})*,\d{2})", joined_header)
    opening_balance = _parse_amount(balances[0]) if balances else Decimal(0)
    closing_balance = _parse_amount(balances[-1]) if balances else Decimal(0)

    account_m = re.search(r"Номер счёта\s+([\d .]+)", joined_header)

    raw_transactions: list[tuple[date, str, Decimal, str]] = []
    pending: tuple[date, str, Decimal] | None = None

    for line in rest:
        if any(noise in line for noise in _SBER_NOISE_SUBSTRINGS):
            continue
        tx_m = _SBER_TX_RE.match(line)
        if tx_m:
            if pending:
                raw_transactions.append(pending)
            amount_raw = tx_m.group(4)
            # В СберБанке пополнение помечается знаком «+», списание печатается
            # без знака; _parse_amount без знака вернёт положительное число.
            amount = _parse_amount(amount_raw)
            if not amount_raw.startswith("+"):
                amount = -amount
            pending = (_parse_date(tx_m.group(1)), "", amount, tx_m.group(3).strip())
            continue
        proc_m = _SBER_PROC_RE.match(line)
        if proc_m:
            if pending:
                pending = (
                    pending[0],
                    (pending[1] + " " + proc_m.group(3)).strip(),
                    pending[2],
                    pending[3],
                )
            continue
        if pending and line.strip():
            # Продолжение описания операции. Посторонние строки-подписи уже отброшены выше.
            pending = (
                pending[0],
                (pending[1] + " " + line.strip()).strip(),
                pending[2],
                pending[3],
            )
    if pending:
        raw_transactions.append(pending)

    transactions = [
        StatementTransaction(
            date=tdate,
            description=description,
            amount=amount,
            category=_categorize(description, amount, sber_category=sber_cat),
        )
        for tdate, description, amount, sber_cat in raw_transactions
    ]

    return ParsedBankStatement(
        bank=STATEMENT_BANK_SBER,
        account_number=account_m.group(1).strip() if account_m else None,
        period_start=period_start,
        period_end=period_end,
        opening_balance=opening_balance,
        closing_balance=closing_balance,
        transactions=transactions,
        **_summarize(transactions, STATEMENT_BANK_SBER),
    )


def _parse_ozon(content: bytes) -> ParsedBankStatement:
    text_lines, tables = _extract_tables(content)
    text = "\n".join(text_lines)

    period_m = re.search(r"Период выписки:\s*(\d{2}\.\d{2}\.\d{4}).*(\d{2}\.\d{2}\.\d{4})", text)
    opening_m = re.search(r"Входящий остаток:\s*([+-]?\s*[\d\s.,]+)\s*₽", text)
    closing_m = re.search(r"Исходящий остаток:\s*([+-]?\s*[\d\s.,]+)\s*₽", text)
    account_m = re.search(r"Номер лицевого счёта:\s*№\s*(\d+)", text)

    raw_transactions: list[tuple[date, str, Decimal]] = []
    for row in tables:
        if not row or len(row) < 5:
            continue
        date_raw, _, description, rub_amount, cur_amount = row[:5]
        if not date_raw or not _DATE_RE.match(date_raw):
            continue
        amount_raw = rub_amount or cur_amount
        if not amount_raw or not _OZON_AMOUNT_RE.match(amount_raw):
            continue
        description = (description or "").replace("\n", " ").strip()
        raw_transactions.append((_parse_date(date_raw.split()[0]), description, _parse_amount(amount_raw)))

    transactions = [
        StatementTransaction(date=tdate, description=description, amount=amount, category=_categorize(description, amount))
        for tdate, description, amount in raw_transactions
    ]

    return ParsedBankStatement(
        bank=STATEMENT_BANK_OZON,
        account_number=account_m.group(1) if account_m else None,
        period_start=_parse_date(period_m.group(1)) if period_m else None,
        period_end=_parse_date(period_m.group(2)) if period_m else None,
        opening_balance=_parse_amount(opening_m.group(1)) if opening_m else Decimal(0),
        closing_balance=_parse_amount(closing_m.group(1)) if closing_m else Decimal(0),
        transactions=transactions,
        **_summarize(transactions, STATEMENT_BANK_OZON),
    )

def _parse_tbank(lines: list[str]) -> ParsedBankStatement:
    text = "\n".join(lines)
    dates = [d for d in re.findall(r"\d{2}\.\d{2}\.\d{2,4}", text) if " " not in d]
    period_start = _parse_date(dates[0]) if dates else None
    period_end = _parse_date(dates[-1]) if dates else None
    
    balances = re.findall(r"Баланс на.*?(?:\|)?\s*([+-]?\s*\d{1,3}(?:[ \u00A0]\d{3})*[.,]\d{2})\s*[PР]", text)
    opening_balance = _parse_amount(balances[0]) if balances else Decimal(0)
    closing_balance = _parse_amount(balances[-1]) if balances else Decimal(0)
    
    transactions = []
    for line in lines:
        if not re.match(r"^\d{2}\.\d{2}\.\d{2,4}", line):
            continue
        amounts = re.findall(rf"{_AMOUNT_RE}\s*[PР]", line)
        if not amounts:
            continue
            
        amount_str = amounts[-1].replace("P", "").replace("Р", "").strip()
        amount = _parse_amount(amount_str)
        
        desc = re.sub(r"\d{2}\.\d{2}\.\d{2,4}(?: \d{2}:\d{2})?", "", line)
        desc = re.sub(rf"{_AMOUNT_RE}\s*[PР]", "", desc).replace("|", "").strip()
        
        if "+" not in amount_str and "Пополнение" not in desc and "Внесение" not in desc and "Перевод с договора" not in desc:
            amount = -abs(amount)
            
        transactions.append(StatementTransaction(
            date=_parse_date(line[:8]), description=desc, amount=amount, category=_categorize(desc, amount)
        ))
        
    return ParsedBankStatement(
        bank="T-Bank", account_number=None, period_start=period_start, period_end=period_end,
        opening_balance=opening_balance, closing_balance=closing_balance, transactions=transactions,
        **_summarize(transactions, "T-Bank")
    )

def detect_bank(content: bytes) -> str:
    joined = "\n".join(_extract_lines(content)).upper()
    
    # Используем только строгие юридические названия и точные заголовки, 
    # чтобы переводы другим банкам внутри списка транзакций не ломали логику.
    if "ООО «ОЗОН БАНК»" in joined: 
        return STATEMENT_BANK_OZON
        
    if "АО «АЛЬФА-БАНК»" in joined: 
        return STATEMENT_BANK_ALFA
        
    if "ВЫПИСКА ПО СЧЁТУ ДЕБЕТОВОЙ КАРТЫ" in joined or "ЗАКАЗАНО В СБЕРБАНК ОНЛАЙН" in joined: 
        return STATEMENT_BANK_SBER
        
    if "ВЫПИСКА ПО ДОГОВОРУ №" in joined or "АКЦИОНЕРНОЕ ОБЩЕСТВО «ТБАНК»" in joined: 
        return STATEMENT_BANK_TBANK
        
    raise UnsupportedStatementError("Банк выписки не распознан")

def parse_statement(content: bytes, filename: str | None = None) -> ParsedBankStatement:
    bank = detect_bank(content)
    if bank == STATEMENT_BANK_OZON:
        return _parse_ozon(content)
    lines = _extract_lines(content)
    if bank == STATEMENT_BANK_ALFA:
        return _parse_alfa(lines)
    if bank == STATEMENT_BANK_SBER:
        return _parse_sber(lines)
    if bank == STATEMENT_BANK_TBANK:
        return _parse_tbank(lines)
    raise UnsupportedStatementError(f"Банк выписки не поддерживается: {bank}")