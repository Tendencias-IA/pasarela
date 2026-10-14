"""Hora del servidor en UTC, sin tzinfo, como la guardan las columnas `DateTime` (MySQL)."""

from __future__ import annotations

from datetime import UTC, datetime


def utcnow() -> datetime:
    """UTC naive: evita depender de la zona horaria de la sesión de MySQL (`now()`)."""
    return datetime.now(UTC).replace(tzinfo=None)
