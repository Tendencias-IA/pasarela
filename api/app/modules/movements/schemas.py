"""Entrada y salida de la API del módulo movements (api-design.md)."""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field
from pydantic import ValidationError as PydanticValidationError

from app.common.errors import ValidationError
from app.common.money import to_json
from app.modules.movements.service import Movement, MovementsPage

PAGE_MESSAGE = "La página debe ser un entero desde 1."


class MovementsQuery(BaseModel):
    """Query string de GET /movements. `from`, `to` y `type` llegan con HU-10; hoy se ignoran."""

    model_config = ConfigDict(extra="ignore")

    page: int = Field(default=1, ge=1)

    @classmethod
    def parse(cls, args: Mapping[str, str]) -> MovementsQuery:
        raw = args.get("page")
        if raw is None:
            return cls()
        text = raw.strip()
        if not (text.isascii() and text.isdigit()):  # "abc", "1.5", "-1", "", "²" → nunca válido
            raise ValidationError("Revisa los campos indicados.", errors=_page_error())
        try:
            return cls(page=int(text))
        except PydanticValidationError:
            raise ValidationError("Revisa los campos indicados.", errors=_page_error()) from None


def _page_error() -> list[dict[str, str]]:
    return [{"field": "page", "message": PAGE_MESSAGE}]


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
