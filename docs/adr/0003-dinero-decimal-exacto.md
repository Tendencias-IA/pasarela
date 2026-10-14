# ADR-0003: Dinero con decimal exacto (`Decimal` / `DECIMAL(15,2)` / cadena en JSON)

**Estado**: Aceptada
**Fecha**: 2026-10-13
**Ticket**: PPA-17

## Contexto

RNF-04.3 exige "una representación decimal exacta apropiada para valores monetarios" y
la definición de terminado prohíbe explícitamente el punto flotante. Los montos son en
COP, con límites entre $100 y $5.000.000, sin saldo máximo.

## Decisión

- Python: `decimal.Decimal`, siempre cuantizado a dos decimales
  (`amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`). Helpers y constantes de
  límites en `backend/app/common/money.py`.
- MySQL: `DECIMAL(15,2)` en `wallets.balance` y `transactions.amount`, con `CHECK
  (balance >= 0)`.
- JSON: los montos viajan como cadena (`"150000.00"`), nunca como número. Pydantic
  parsea la cadena a `Decimal` en entrada y la serializa de vuelta en salida.
- Frontend: los montos se manejan como cadena y se formatean con `Intl.NumberFormat`
  para `es-CO`; la aritmética en el navegador se limita a mostrar, nunca a decidir.

## Alternativas consideradas

- **Enteros en centavos**: exacto y rápido, pero el documento de requisitos pide
  representación decimal y el COP se expresa en pesos enteros, lo que haría confusa la
  conversión en pruebas y en revisiones.
- **`float` / `DOUBLE`**: rechazado; `0.1 + 0.2 != 0.3` y la definición de terminado lo
  prohíbe.

## Consecuencias

- Toda prueba de montos compara `Decimal` con `Decimal`, no con literales numéricos.
- Ruff y mypy se configuran para que `float` en `money.py`, `service.py` de `wallet` y
  `transfers` sea un error de revisión (ver `.claude/rules/backend.md`).
