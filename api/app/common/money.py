"""Dinero con decimal exacto (ADR-0003, RNF-04.3). Única fuente de los límites de negocio."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

TWO_PLACES = Decimal("0.01")
MAX_DIGITS = 15

TRANSFER_MIN, TRANSFER_MAX = Decimal("100.00"), Decimal("3000000.00")
RECHARGE_MIN, RECHARGE_MAX = Decimal("5000.00"), Decimal("5000000.00")

AMOUNT_FORMAT_MESSAGE = "El monto debe ser un número positivo con hasta dos decimales."


def quantize(amount: Decimal) -> Decimal:
    """Normaliza a dos decimales con redondeo comercial (solo para valores ya válidos)."""
    return amount.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def parse_amount(value: object) -> Decimal:
    """Convierte la cadena de un cliente en `Decimal` positivo con hasta dos decimales.

    Rechaza números JSON (deben llegar como cadena), vacío, signos, notación científica,
    NaN/Infinity y más de dos decimales. Lanza `ValueError` con mensaje en español.
    """
    if not isinstance(value, str):
        raise ValueError(AMOUNT_FORMAT_MESSAGE)
    text = value.strip()
    digits = text.replace(".", "", 1)
    # `isdigit()` acepta dígitos Unicode (árabes, de ancho completo…); el contrato exige ASCII.
    if not text or any(ch in text for ch in "+-eE") or not (digits.isascii() and digits.isdigit()):
        raise ValueError(AMOUNT_FORMAT_MESSAGE)
    try:
        amount = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(AMOUNT_FORMAT_MESSAGE) from exc
    exponent = amount.as_tuple().exponent
    if not isinstance(exponent, int) or exponent < -2 or amount <= 0:
        raise ValueError(AMOUNT_FORMAT_MESSAGE)
    if len(amount.as_tuple().digits) - max(0, -exponent) > MAX_DIGITS - 2:
        raise ValueError(AMOUNT_FORMAT_MESSAGE)
    return quantize(amount)


def to_json(amount: Decimal) -> str:
    """Representación de salida: cadena con exactamente dos decimales."""
    return f"{quantize(amount):f}"
