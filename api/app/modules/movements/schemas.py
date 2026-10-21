"""Entrada y salida de la API del módulo movements (api-design.md)."""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.common.errors import ValidationError
from app.common.money import to_json
from app.modules.movements.repository import MovementsFilter, MovementType
from app.modules.movements.service import Movement, MovementsPage

PAGE_MESSAGE = "La página debe ser un entero desde 1."
DATE_MESSAGE = "La fecha debe tener el formato AAAA-MM-DD."
TYPE_MESSAGE = "El tipo debe ser all, sent, received o recharge."
_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}", re.ASCII)


class MovementsQuery(BaseModel):
    """Query string de GET /movements: página (HU-09) y filtros from, to, type (HU-10)."""

    model_config = ConfigDict(extra="ignore")

    page: int = Field(default=1, ge=1)
    from_: date | None = None
    to: date | None = None
    type_: MovementType = MovementType.ALL

    @property
    def filters(self) -> MovementsFilter:
        return MovementsFilter(from_=self.from_, to=self.to, type_=self.type_)

    @classmethod
    def parse(cls, args: Mapping[str, str]) -> MovementsQuery:
        """Valida todo a la vez (RNF-03.2). `from > to` lo decide el servicio (HU-10 CA-2)."""
        errors: list[dict[str, str]] = []
        page = _parse_page(args.get("page"), errors)
        from_ = _parse_date("from", args.get("from"), errors)
        to = _parse_date("to", args.get("to"), errors)
        type_ = _parse_type(args.get("type"), errors)
        if errors:
            raise ValidationError("Revisa los campos indicados.", errors=errors)
        return cls(page=page, from_=from_, to=to, type_=type_)


def _parse_page(raw: str | None, errors: list[dict[str, str]]) -> int:
    if raw is None:
        return 1
    text = raw.strip()
    # "abc", "1.5", "-1", "", "²" → nunca válido
    if text.isascii() and text.isdigit() and int(text) >= 1:
        return int(text)
    errors.append({"field": "page", "message": PAGE_MESSAGE})
    return 1


def _parse_date(field: str, raw: str | None, errors: list[dict[str, str]]) -> date | None:
    if raw is None:
        return None
    if _DATE_PATTERN.fullmatch(raw):
        try:
            return date.fromisoformat(raw)
        except ValueError:  # "2026-02-31": con forma de fecha pero inexistente
            pass
    errors.append({"field": field, "message": DATE_MESSAGE})
    return None


def _parse_type(raw: str | None, errors: list[dict[str, str]]) -> MovementType:
    if raw is None:
        return MovementType.ALL
    try:
        return MovementType(raw)
    except ValueError:
        errors.append({"field": "type", "message": TYPE_MESSAGE})
        return MovementType.ALL


class CounterpartyOut(BaseModel):
    name_masked: str | None
    phone_masked: str


class MovementOut(BaseModel):
    id: int
    direction: str
    type: str
    status: str
    amount: str
    created_at: str
    rejection_reason: str | None
    counterparty: CounterpartyOut | None

    @classmethod
    def from_movement(cls, movement: Movement) -> MovementOut:
        counterparty = movement.counterparty
        return cls(
            id=movement.id,
            direction=movement.direction.value,
            type=movement.type.value,
            status=movement.status.value,
            amount=to_json(movement.amount),
            created_at=movement.created_at.replace(microsecond=0).isoformat() + "Z",
            rejection_reason=movement.rejection_reason,
            counterparty=None
            if counterparty is None
            else CounterpartyOut(
                name_masked=counterparty.name_masked, phone_masked=counterparty.phone_masked
            ),
        )


class MovementsPageOut(BaseModel):
    items: list[MovementOut]
    page: int
    page_size: int
    total: int

    @classmethod
    def from_page(cls, page: MovementsPage) -> MovementsPageOut:
        return cls(
            items=[MovementOut.from_movement(m) for m in page.items],
            page=page.page,
            page_size=page.page_size,
            total=page.total,
        )
