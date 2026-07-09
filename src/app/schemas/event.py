"""Schemas de Eventos/Compromissos da Agenda."""

import uuid
from datetime import datetime

from pydantic import Field, field_serializer, model_validator

from app.schemas.common import ORMModel


class EventCreate(ORMModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    start_at: datetime
    end_at: datetime
    all_day: bool = False
    location: str | None = None
    color: str | None = None
    recurrence_rule: str | None = None
    category_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    google_account_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _check_range(self) -> "EventCreate":
        if self.end_at <= self.start_at:
            raise ValueError("end_at deve ser posterior a start_at")
        return self

    @model_validator(mode="after")
    def _check_recurrence_vs_google(self) -> "EventCreate":
        if self.recurrence_rule and self.google_account_id:
            raise ValueError("Compromissos recorrentes não podem ser sincronizados com o Google Calendar.")
        return self


class EventUpdate(ORMModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    all_day: bool | None = None
    location: str | None = None
    color: str | None = None
    recurrence_rule: str | None = None
    category_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    google_account_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _check_recurrence_vs_google(self) -> "EventUpdate":
        # Patch parcial: só valida quando os DOIS campos vierem juntos no
        # mesmo payload — a combinação com o estado já persistido (payload
        # setando só um dos dois) é validada em EventService.update, que
        # tem acesso ao registro atual.
        if self.recurrence_rule and self.google_account_id:
            raise ValueError("Compromissos recorrentes não podem ser sincronizados com o Google Calendar.")
        return self


class EventRead(ORMModel):
    id: uuid.UUID
    title: str
    description: str | None
    start_at: datetime
    end_at: datetime
    all_day: bool
    location: str | None
    color: str | None
    recurrence_rule: str | None
    meeting_link: str | None
    category_id: uuid.UUID | None
    project_id: uuid.UUID | None
    google_account_id: uuid.UUID | None
    google_event_id: str | None
    has_conflict: bool = False

    @field_serializer("start_at", "end_at", when_used="json")
    def _serialize_utc(self, value: datetime) -> str:
        """Event.start_at/end_at são sempre naive-UTC no banco (ver
        Event._validate_datetime) — sem o "Z" explícito aqui, o JSON não diz
        que é UTC e o FullCalendar no browser interpreta como horário local,
        aplicando o fuso duas vezes (ex.: BRT vira +3h adiantado). `when_used`
        restrito a "json" evita corromper `_to_read`, que faz
        `.model_dump()` (modo python) e reconstrói o EventRead em seguida —
        se o serializer rodasse aí também, o valor viraria string, seria
        reparsado como aware, e um "Z" seria concatenado de novo em cima do
        offset já presente. Eventos dia-inteiro (`all_day`) não têm horário
        significativo — o Google já manda só a data — então ficam sem "Z"
        pro FullCalendar tratar como data "flutuante" em vez de instante.
        """
        if self.all_day:
            return value.isoformat()
        return value.isoformat() + "Z"
