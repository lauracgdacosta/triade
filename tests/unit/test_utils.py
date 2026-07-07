"""Testes unitários de utilitários (datetime, sanitização, paginação)."""

from datetime import date, datetime

from app.utils.datetime_utils import end_of_week, ranges_overlap, start_of_week
from app.utils.pagination import Page, PageParams
from app.utils.sanitize import sanitize_html


def test_start_of_week_monday_first():
    reference = date(2026, 1, 7)  # quarta-feira
    assert start_of_week(reference, week_start_monday=True) == date(2026, 1, 5)


def test_start_of_week_sunday_first():
    reference = date(2026, 1, 7)  # quarta-feira
    assert start_of_week(reference, week_start_monday=False) == date(2026, 1, 4)


def test_end_of_week():
    reference = date(2026, 1, 5)  # segunda-feira
    assert end_of_week(reference, week_start_monday=True) == date(2026, 1, 11)


def test_ranges_overlap_true():
    a_start, a_end = datetime(2026, 1, 1, 9), datetime(2026, 1, 1, 10)
    b_start, b_end = datetime(2026, 1, 1, 9, 30), datetime(2026, 1, 1, 10, 30)
    assert ranges_overlap(a_start, a_end, b_start, b_end) is True


def test_ranges_overlap_false_when_adjacent():
    a_start, a_end = datetime(2026, 1, 1, 9), datetime(2026, 1, 1, 10)
    b_start, b_end = datetime(2026, 1, 1, 10), datetime(2026, 1, 1, 11)
    assert ranges_overlap(a_start, a_end, b_start, b_end) is False


def test_sanitize_html_strips_script_tags():
    dirty = '<p>Olá</p><script>alert(1)</script>'
    clean = sanitize_html(dirty)
    assert "<script>" not in clean
    assert "<p>Olá</p>" in clean


def test_sanitize_html_none_passthrough():
    assert sanitize_html(None) is None


def test_page_params_offset():
    params = PageParams(page=3, page_size=10)
    assert params.offset == 20


def test_page_total_pages():
    page = Page(items=[1, 2], total=25, page=1, page_size=10)
    assert page.total_pages == 3
