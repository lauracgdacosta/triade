"""Helpers de data/hora usados pelo Dashboard e pela Agenda."""

from datetime import UTC, date, datetime, timedelta


def utcnow() -> datetime:
    """Agora em UTC, *naive* (sem tzinfo).

    As colunas de datetime "de negócio" deste projeto (`Task.completed_at`,
    `Event.start_at`/`end_at`, `PomodoroSession.started_at`/`ended_at`,
    `TimeEntry.start_at`/`end_at`) são `timestamp without time zone` no
    Postgres — não timezone-aware. Fazer bind de um `datetime` com `tzinfo`
    contra elas quebra no asyncpg em runtime ("can't subtract offset-naive
    and offset-aware datetimes"), algo que não aparece testando com SQLite
    (que não distingue os dois casos). Use esta função — não
    `datetime.now(UTC)` — para qualquer valor que seja gravado nessas
    colunas ou comparado com elas. (`TimestampMixin.created_at/updated_at`
    são a exceção — essas *são* `DateTime(timezone=True)`.)
    """
    return datetime.now(UTC).replace(tzinfo=None)


def start_of_week(reference: date, week_start_monday: bool = True) -> date:
    weekday = reference.weekday()  # segunda=0 ... domingo=6
    if not week_start_monday:
        weekday = (weekday + 1) % 7
    return reference - timedelta(days=weekday)


def end_of_week(reference: date, week_start_monday: bool = True) -> date:
    return start_of_week(reference, week_start_monday) + timedelta(days=6)


def ranges_overlap(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
    return start_a < end_b and start_b < end_a


# Nomes fixos por prefixo de idioma (em vez de `locale.setlocale`, que é global ao
# processo e não é seguro num servidor async multiusuário — mutaria o locale de
# todas as requisições concorrentes, não só a do usuário atual).
_WEEKDAYS = {
    "pt": ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "es": ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"],
}
_MONTHS = {
    "pt": [
        "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
    ],
    "en": [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ],
    "es": [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    ],
}


def _language_prefix(locale: str) -> str:
    return locale.split("-")[0].lower()


def format_long_date(reference: date, locale: str = "pt-BR") -> str:
    lang = _language_prefix(locale)
    weekdays = _WEEKDAYS.get(lang, _WEEKDAYS["pt"])
    months = _MONTHS.get(lang, _MONTHS["pt"])
    weekday = weekdays[reference.weekday()]
    month = months[reference.month - 1]
    if lang == "en":
        return f"{weekday}, {month} {reference.day}, {reference.year}"
    if lang == "es":
        return f"{weekday}, {reference.day} de {month} de {reference.year}"
    return f"{weekday}, {reference.day} de {month} de {reference.year}"


def format_short_date(reference: date, locale: str = "pt-BR") -> str:
    if _language_prefix(locale) == "en":
        return reference.strftime("%m/%d/%Y")
    return reference.strftime("%d/%m/%Y")
