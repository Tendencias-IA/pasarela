# Research: Consultar el saldo (HU-05)

Fase 0 del plan. Las decisiones 1, 2 y 5 vienen del borrador de moagu
(`feat/PPA-5-consultar-el-saldo`) y se confirmaron; la 3 se corrigió; la 4 se reescribió
para encajar con el panel y TanStack Query que HU-09 ya dejó en la webapp.

## 1. La titularidad se deriva de la sesión

- **Decisión**: `GET /api/v1/wallet` no recibe id de usuario ni de billetera. La ruta exige
  `@login_required` y pasa al servicio solo `current_user_id()`; cualquier parámetro de
  query se ignora.
- **Razón**: HU-05 CA-1 y CA-4, RNF-01.1, RNF-01.4, RNF-06.1. `app/common/auth.py` ya
  resuelve la sesión server-side de HU-02.
- **Alternativas**: aceptar `user_id`/`wallet_id` (rechazado: permitiría intentar leer otra
  cuenta y no está en la especificación); rutas `/users/{id}/wallet` (prohibidas por
  `security.md`).

## 2. La billetera es propiedad del módulo `wallet`; la lectura no escribe

- **Decisión**: reutilizar `wallets` y el modelo `Wallet` de HU-08. El servicio
  `wallet_service.get_balance(user_id) -> Decimal` usa `repository.get_wallet_by_user`
  (sin `FOR UPDATE`, sin `with transaction()`), y lanza `WalletNotFoundError` (ya existe)
  si no hay billetera, tras un `log.warning("wallet.missing", extra={"user_id": ...})`.
- **Razón**: `architecture.md` asigna HU-05 a `wallet`. Una lectura con bloqueo
  serializaría consultas con recargas y degradaría RNF-02.1 sin aportar nada: el saldo
  leído es consistente por sí mismo en `READ COMMITTED`. CA-5 pide registrar el error
  técnico: `WARNING` porque es un dato inconsistente, no un fallo del sistema.
- **Alternativas**: crear la billetera al consultar (rechazado: convierte lectura en
  escritura y contradice CA-5); devolver `0.00` sin billetera (rechazado: falso).

## 3. Contrato: `200 {"balance"}`, `404 wallet_not_found`, `401 invalid_session`

- **Decisión**: éxito `200 {"balance": "150000.00"}` con `to_json` de
  `app/common/money.py` (cadena, dos decimales). Billetera ausente `404` RFC 9457 con
  `code: wallet_not_found`. Sin sesión `401` con `code: invalid_session`, el mismo que
  usan HU-08 y HU-09 y que `shared/api/client.ts` convierte en redirección a `/login`.
  Schema de salida `WalletOut` en `wallet/schemas.py` (nombre del recurso, como
  `RechargeOut`).
- **Razón**: `api-design.md` fija exactamente esa fila para HU-05. El borrador renombraba
  `invalid_session` a `unauthenticated` en `auth`, `client.ts` y seis suites; se descartó
  porque la regla fijó `invalid_session` en PPA-8 (`b871751`) y el cambio rompería HU-04,
  HU-08 y HU-09 en paralelo.
- **Alternativas**: saldo numérico (rechazado por RNF-04.3 y ADR-0003); `403` para "no es
  tuyo" (no aplica: no hay recurso ajeno direccionable).

## 4. Tarjeta de saldo en la pantalla principal con TanStack Query

- **Decisión**: `features/wallet/useWallet.ts` con `useQuery({ queryKey: ["wallet"] })`
  y `WALLET_QUERY_KEY` exportada; `features/wallet/api.ts` añade `getWallet()`.
  `app/HomePage.tsx` muestra una tarjeta "Saldo disponible" con `formatCOP(balance)`,
  estado "Consultando saldo…" (`role="status"`), "Saldo no disponible" ante
  `404 wallet_not_found` (`role="alert"`) y "No se pudo consultar el saldo" con
  "Reintentar" ante otros errores. `useRecharge.ts` invalida `["wallet"]` además de
  `["movements"]` tras un `201`. El `401` ya redirige a `/login` vía `client.ts`.
- **Razón**: RF-03 dice "el usuario abre la pantalla principal"; `webapp.md` exige
  TanStack Query para estado del servidor e invalidar la query de saldo tras recargas
  (HU-05 CA-3). HU-09 ya montó `QueryClientProvider`, así que no hay infraestructura nueva.
  La tarjeta de estado de la API se conserva: el smoke test del esqueleto la usa y no es
  de esta historia.
- **Alternativas**: una `BalancePage` propia en `/` (borrador; rechazado: duplica la
  pantalla principal y los accesos a recargar y movimientos que ya tiene `HomePage`);
  mostrar `balance_after` de la recarga como fuente del panel (rechazado: la pantalla de
  recarga ya lo muestra; el panel debe leer el valor persistido, CA-2).

## 5. Rendimiento se verifica con carga, no con la UI

- **Decisión**: añadir `@task` `GET /api/v1/wallet` al `locustfile.py` (ya hace login en
  `on_start`) y verificar p95 ≤ 2000 ms en el job nocturno (RNF-02.1).
- **Razón**: HU-05 CA-6 es una métrica de sistema bajo carga; `quality-gates.md` ya lista
  ese umbral para `GET /api/v1/wallet`.

## 6. Pantalla principal privada y smoke test

- **Decisión**: al mostrar el saldo, abrir `/` sin sesión produce un `401` que redirige a
  `/login` (comportamiento ya definido en `client.ts`). `webapp/e2e/smoke.spec.ts`
  inicia sesión antes de abrir `/` y localiza el estado de la API por su texto, no por
  `getByRole("status")` genérico (ahora hay más de un `status` en la página).
- **Razón**: RNF-01.1: todo lo que no sea registro, login y health es privado.
