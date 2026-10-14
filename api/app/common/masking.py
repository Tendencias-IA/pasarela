"""Enmascaramiento de datos de terceros (RNF-06, HU-06 CA-7, HU-09 CA-3).

Se aplica siempre en el servidor: lo que llega al navegador es público (security.md).
"""

from __future__ import annotations

HIDDEN = "***"


def mask_phone(phone: str) -> str:
    """`"3001234567"` → `"***4567"`; con menos de cuatro dígitos, solo `"***"`."""
    digits = phone.strip()
    if len(digits) < 4:
        return HIDDEN
    return HIDDEN + digits[-4:]


def mask_name(full_name: str | None) -> str:
    """`"Maria Garcia"` → `"Mar** G*****"`: tres letras de la primera palabra, inicial del resto."""
    words = (full_name or "").split()
    if not words:
        return HIDDEN
    first, *rest = words
    masked = [first[:3] + "*" * max(0, len(first) - 3)]
    masked.extend(word[0] + "*" * (len(word) - 1) for word in rest)
    return " ".join(masked)
