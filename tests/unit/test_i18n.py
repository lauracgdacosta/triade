"""Testes do utilitário de i18n: fallback de locale/chave e localização de datas."""

from datetime import date

from app.utils.datetime_utils import format_long_date, format_short_date
from app.utils.i18n import t


def test_t_translates_known_key_in_each_locale():
    assert t("nav.tasks", "pt-BR") == "Tarefas"
    assert t("nav.tasks", "en-US") == "Tasks"
    assert t("nav.tasks", "es-ES") == "Tareas"


def test_t_falls_back_to_default_locale_when_locale_missing():
    assert t("nav.tasks", "fr-FR") == "Tarefas"


def test_t_falls_back_to_key_itself_when_key_missing_everywhere():
    assert t("nonexistent.key", "pt-BR") == "nonexistent.key"


def test_format_short_date_uses_locale_specific_order():
    reference = date(2026, 3, 5)
    assert format_short_date(reference, "pt-BR") == "05/03/2026"
    assert format_short_date(reference, "en-US") == "03/05/2026"


def test_format_long_date_uses_locale_specific_month_names():
    reference = date(2026, 3, 5)  # quinta-feira
    assert "março" in format_long_date(reference, "pt-BR")
    assert "March" in format_long_date(reference, "en-US")
    assert "marzo" in format_long_date(reference, "es-ES")
