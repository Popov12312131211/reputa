import os
from datetime import date
from decimal import Decimal

import pytest

from app.core.constants import (
    STATEMENT_BANK_ALFA,
    STATEMENT_BANK_OZON,
    STATEMENT_BANK_SBER,
    STMT_CATEGORY_INCOME,
)
from app.scoring.stmt_parser import (
    StatementParseError,
    UnsupportedStatementError,
    _parse_amount,
    detect_bank,
    parse_statement,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _fixture(name: str) -> bytes:
    with open(os.path.join(FIXTURES_DIR, f"{name}.pdf"), "rb") as fh:
        return fh.read()


def _minimal_pdf(text: str) -> bytes:
    """Собирает минимальный валидный PDF с одной страницей и заданным текстом."""
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    obj1 = b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    obj2 = b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    obj3 = b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj\n"
    obj4 = (
        b"4 0 obj<</Length "
        + str(len(stream)).encode()
        + b">>stream\n"
        + stream
        + b"\nendstream\nendobj\n"
    )
    return b"%PDF-1.4\n" + obj1 + obj2 + obj3 + obj4 + b"trailer<</Root 1 0 R/Size 5>>\nstartxref\n0\n%%EOF\n"


class TestDetectBank:
    def test_alfa(self):
        assert detect_bank(_fixture("alfa")) == STATEMENT_BANK_ALFA

    def test_sber(self):
        # В выписке СберБанка в описаниях встречается «Альфа-Банк», поэтому
        # распознавание не должно опираться только на эту подстроку.
        assert detect_bank(_fixture("sber")) == STATEMENT_BANK_SBER

    def test_ozon(self):
        assert detect_bank(_fixture("ozon")) == STATEMENT_BANK_OZON

    def test_unsupported_raises(self):
        # Валидный PDF, но без признаков известного банка.
        with pytest.raises(UnsupportedStatementError):
            detect_bank(_minimal_pdf("Some bank statement"))


class TestParseAmount:
    def test_negative_russian_format(self):
        assert _parse_amount("-1 234,56") == Decimal("-1234.56")

    def test_positive_with_plus(self):
        assert _parse_amount("+4 698,00") == Decimal("4698.00")

    def test_unsigned(self):
        assert _parse_amount("46,00") == Decimal("46.00")

    def test_nbsp_thousands(self):
        assert _parse_amount("9 652,00") == Decimal("9652.00")

    def test_ozon_format_with_currency(self):
        assert _parse_amount("- 1 000.00 ₽") == Decimal("-1000.00")


class TestParseStatementAlfa:
    @pytest.fixture
    def statement(self):
        return parse_statement(_fixture("alfa"), filename="alfa.pdf")

    def test_bank(self, statement):
        assert statement.bank == STATEMENT_BANK_ALFA
    def test_account(self, statement):
        assert statement.account_number == "40817810305972810793"

    def test_period(self, statement):
        assert statement.period_start == date(2026, 6, 5)
        assert statement.period_end == date(2026, 9, 5)

    def test_balances(self, statement):
        assert statement.opening_balance == Decimal("1776.84")
        assert statement.closing_balance == Decimal("2614.63")

    def test_totals_match_header(self, statement):
        assert statement.income == Decimal("118530.00")
        assert statement.expenses == Decimal("117692.21")

    def test_transactions(self, statement):
        assert statement.transactions
        assert all(tx.amount != 0 for tx in statement.transactions)
        assert all(tx.description for tx in statement.transactions)

    def test_income_category(self, statement):
        incomes = [tx for tx in statement.transactions if tx.amount > 0]
        assert all(tx.category == STMT_CATEGORY_INCOME for tx in incomes)

    def test_expenses_by_category(self, statement):
        assert statement.expenses_by_category
        assert sum(statement.expenses_by_category.values()) == statement.expenses


class TestParseStatementSber:
    @pytest.fixture
    def statement(self):
        return parse_statement(_fixture("sber"), filename="sber.pdf")

    def test_bank(self, statement):
        assert statement.bank == STATEMENT_BANK_SBER

    def test_period(self, statement):
        assert statement.period_start == date(2026, 6, 1)
        assert statement.period_end == date(2026, 9, 1)

    def test_balances(self, statement):
        assert statement.opening_balance == Decimal("0.30")
        assert statement.closing_balance == Decimal("9652.00")

    def test_totals_match_header(self, statement):
        assert statement.income == Decimal("104693.16")
        assert statement.expenses == Decimal("95041.46")

    def test_transactions(self, statement):
        expenses = [tx for tx in statement.transactions if tx.amount < 0]
        assert expenses
        assert len(statement.transactions) == 54

    def test_expenses_by_category(self, statement):
        assert sum(statement.expenses_by_category.values()) == statement.expenses


class TestParseStatementOzon:
    @pytest.fixture
    def statement(self):
        return parse_statement(_fixture("ozon"), filename="ozon.pdf")

    def test_bank(self, statement):
        assert statement.bank == STATEMENT_BANK_OZON

    def test_account(self, statement):
        assert statement.account_number == "40817810500008702515"

    def test_period(self, statement):
        assert statement.period_start == date(2026, 6, 4)
        assert statement.period_end == date(2026, 9, 4)

    def test_totals_match_footer(self, statement):
        assert statement.income == Decimal("89787.16")
        assert statement.expenses == Decimal("89787.16")

    def test_balances(self, statement):
        assert statement.opening_balance == Decimal("0.00")
        assert statement.closing_balance == Decimal("0.00")

    def test_expenses_by_category(self, statement):
        assert sum(statement.expenses_by_category.values()) == statement.expenses


class TestParseStatementErrors:
    def test_empty_content_raises(self):
        with pytest.raises(StatementParseError):
            parse_statement(b"")

    def test_garbage_raises_unsupported(self):
        with pytest.raises(UnsupportedStatementError):
            parse_statement(_minimal_pdf("Some bank statement"))

    def test_text_pdf_with_unknown_bank_raises(self):
        # Небинарный мусор падает на этапе чтения файла (StatementParseError).
        with pytest.raises(StatementParseError):
            parse_statement("Просто текст без признаков выписки".encode("utf-8"))