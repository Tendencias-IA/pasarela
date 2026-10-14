# Research: Historial de movimientos (HU-09)

Fase 0 del plan. Cada punto resuelve una duda del Technical Context o fija cómo se aplica
una regla ya existente del proyecto a esta historia.

## 1. Cómo obtiene `movements` la billetera del usuario y la contraparte sin tocar tablas ajenas

- **Decisión**: el módulo `movements` solo consulta `transactions` (compartida, ADR-0006)
  desde su propio `repository.py`. La billetera del usuario la pide a
  `wallet_service.get_wallet_id(user_id)` (ya existe). Para la contraparte de una
  transferencia, el servicio reúne los `wallet_id` ajenos de la página y llama a una
  función nueva `wallet_service.get_wallet_owners(wallet_ids) -> dict[int, WalletOwner]`,
  que dentro del módulo `wallet` resuelve `wallets → user_id` y pide a
  `accounts_service.get_users_by_ids(user_ids)` los datos del titular. El servicio de
  `movements` enmascara y arma la respuesta.
- **Razón**: la constitución (IV) y `architecture.md` prohíben importar `models.py` o
  `repository.py` de otro módulo. Son tres consultas por página (transacciones + total,
  billeteras, usuarios), acotadas a 20 ids: coste despreciable frente a RNF-02.2.
- **Alternativas**: un único `JOIN transactions → wallets → users` en el repositorio de
  `movements` (rechazado: acopla tres módulos en una consulta, exactamente lo que ADR-0001
  y ADR-0006 evitan); duplicar `phone` en `transactions` (rechazado: desnormaliza datos
  personales y los deja sin enmascarar en una tabla compartida).

## 2. Enmascaramiento en servidor: `app/common/masking.py`

- **Decisión**: crear `app/common/masking.py` con `mask_phone(phone) -> "***4567"`
  (últimos cuatro dígitos, `"***"` si tiene menos de cuatro) y `mask_name(full_name) ->
  "Mar** G****"` (tres primeras letras de la primera palabra y la inicial del resto, cada
  parte completada con `*` hasta su longitud original; `"***"` si viene vacío). El módulo
  `auth` tiene hoy un `_mask_phone` privado para logs; no se toca (otro dueño), pero el PR
  avisa para que lo reemplace cuando convenga.
- **Razón**: `architecture.md` ya ubica ambas funciones en ese archivo y fija el formato de
  ejemplo (HU-06 CA-7, RNF-06). HU-06 reutilizará el mismo módulo para el "preview".
- **Alternativas**: enmascarar en la webapp (rechazado por `security.md`: lo que llega al
  navegador es público).

## 3. `users` todavía no tiene `full_name`

- **Decisión**: `users` solo tiene `phone` y `password_hash` (HU-02); `full_name` lo añade
  HU-01 (Melanny, en progreso). El contrato define la contraparte como
  `{"name_masked": string | null, "phone_masked": string}`: hoy `name_masked` es `null`
  y `accounts_service.get_users_by_ids` devuelve `UserSummary(id, phone, full_name=None)`.
  Cuando HU-01 llegue a `main`, basta que `accounts` llene `full_name` en ese resumen; el
  resto de la cadena, la prueba de `mask_name` y la pantalla ("***" si es `null`) ya lo
  contemplan.
- **Razón**: no se puede añadir la columna desde esta HU sin pisar la migración de HU-01;
  CA-3 se cumple con el teléfono enmascarado y queda el hueco explícito y probado.
- **Alternativas**: esperar a HU-01 (bloquea sin necesidad); migración propia (conflicto de
  Alembic seguro).

## 4. Paginación: fija de 20, `page` desde 1, página fuera de rango

- **Decisión**: `GET /api/v1/movements?page=N`. `page` es opcional (por defecto 1), entero
  `>= 1`; `"0"`, `"-1"` o `"abc"` responden `422 validation` con `errors[{field: "page"}]`.
  Una página mayor que la última responde `200` con `items: []` y el `total` real. La
  respuesta es `{items, page, page_size: 20, total}`; `total` se calcula con `COUNT(*)`
  en la misma condición. Sin `page_size` por query ni cursores.
- **Razón**: RF-05 fija 20; `api-design.md` prohíbe `page_size` y `offset` libres. Un
  `COUNT` por consulta sobre índices `(receiver_wallet_id, created_at)` y
  `(sender_wallet_id, created_at)` es suficiente para el volumen del prototipo. Un "más
  allá del final" no es un error del usuario (puede pasar al borrar/reordenar), así que la
  interfaz corrige llevándolo a la última página.
- **Alternativas**: cursores por `(created_at, id)` (más robusto ante inserciones
  concurrentes, pero CA-6 pide "avanzar o retroceder" con páginas numeradas; se descarta
  en v1.0); `404 page_not_found` para páginas vacías (rechazado: obliga a la webapp a
  tratar un caso normal como error).

## 5. Orden estable

- **Decisión**: `ORDER BY created_at DESC, id DESC`. La condición de titularidad es
  `sender_wallet_id = :w OR (receiver_wallet_id = :w AND (type = recarga OR status =
  exitosa))`: una transferencia rechazada solo la ve quien la intentó (la billetera
  destino nunca la recibió), mientras que una recarga rechazada sí es del titular.
- **Razón**: CA-4 y el edge case de fechas iguales: `created_at` tiene precisión de
  segundos en el esquema actual (`DATETIME`), así que dos recargas en el mismo segundo
  necesitan el desempate por `id` para no repetirse ni perderse entre páginas.
- **Alternativas**: solo `created_at` (rechazado por lo anterior).

## 6. Proyección "enviada / recibida / recarga" y estado

- **Decisión**: el servicio deriva `direction` por fila: `recarga` si `type = recarga`;
  `enviada` si `sender_wallet_id` es la billetera del usuario; `recibida` si lo es
  `receiver_wallet_id`. El `status` y `rejection_reason` se exponen tal cual. Una
  transferencia rechazada solo tiene `sender_wallet_id = usuario` (la billetera destino
  no se vio afectada), así que naturalmente aparece solo para quien la intentó.
- **Razón**: FR-003, FR-002 y "Estados de una operación" de `architecture.md`; no se
  duplican filas por participante.

## 7. Estado del servidor en la webapp: TanStack Query

- **Decisión**: añadir `@tanstack/react-query` (está en la lista permitida de
  `webapp.md`, no requiere ADR nuevo) en un commit propio `build(PPA-9)`. `App.tsx` monta
  un `QueryClientProvider`; `useMovements(page)` usa `useQuery` con clave
  `["movements", page]` y `placeholderData: keepPreviousData` para que cambiar de página
  no vacíe la lista. HU-08 (`useRecharge`) invalida `["movements"]` tras una recarga
  exitosa, como pide `webapp.md`.
- **Razón**: `webapp.md` fija TanStack Query para saldo, movimientos y perfil; esta es la
  primera consulta de servidor con caché e invalidación, y HU-05 (saldo) la reutilizará.
- **Alternativas**: `useEffect` + `useState` como en `HomePage` (rechazado: no hay
  invalidación ni caché entre páginas, y contradice la regla escrita).

## 8. Fechas

- **Decisión**: el servidor entrega `created_at` en ISO 8601 UTC con sufijo `Z`, como ya
  hace `RechargeOut`; la webapp lo muestra con `Intl.DateTimeFormat("es-CO", {dateStyle:
  "medium", timeStyle: "short"})` en la zona del navegador, mediante
  `shared/dates/formatDateTime`.
- **Razón**: coherencia con HU-08; RNF-03.

## 9. Pruebas

- **Decisión**: unitarias de `movements.service` con `FakeMovementsRepository` (orden,
  dirección, enmascaramiento, paginación aritmética, billetera inexistente → vacío);
  integración MySQL con 45 movimientos sembrados por una factory nueva
  `make_transaction(...)` en `tests/factories.py` (recargas y transferencias entre dos
  usuarios, con `created_at` controlado): titularidad (A no ve lo de B), orden estable,
  tres páginas sin repetidos; contrato contra `openapi.yaml` (`MovementsPage`); `e2e_api`
  con login real; Vitest de `useMovements` (MSW) y `MovementsPage` (lista, vacío,
  paginación, 401); Playwright `hu-09-historial-movimientos.spec.ts` con login real: hace
  una recarga por la API o por la pantalla de HU-08 y la ve en el historial, estado vacío
  con un usuario nuevo sembrado para E2E, axe.
- **Razón**: constitución III; `testing.md`.
- **Detalle**: el seed de E2E crea un segundo usuario sin movimientos (`3009876544`) para
  el estado vacío; el usuario existente acumula recargas entre corridas, lo que sirve para
  probar paginación real cuando supere 20.

## 10. Rendimiento (CA-8)

- **Decisión**: dos consultas indexadas por página (lista y `COUNT`) más dos consultas
  por ids; p95 esperado muy por debajo de 3 s. Se añade `GET /api/v1/movements` al
  `locustfile.py` con login real por `/api/v1/auth/login` (peso 1, como las consultas).
- **Razón**: RNF-02.2; el job nocturno verifica el p95 por endpoint.
