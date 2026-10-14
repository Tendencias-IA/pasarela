# Research: Consultar el saldo

## Decision 1: La titularidad se deriva de la sesión

**Decision**: `GET /api/v1/wallet` no recibe un id de usuario ni de billetera. La ruta
exige `@login_required` y pasa al servicio únicamente el id del usuario obtenido de la
sesión actual.

**Rationale**: Cumple HU-05 CA-1 y CA-4, RNF-01.1, RNF-01.4 y RNF-06.1. La rama ya tiene
`app.common.auth.current_user()` y sesiones del lado del servidor implementadas por
HU-02.

**Alternatives considered**:

- Aceptar `user_id` o `wallet_id` en URL, query o cuerpo: rechazado porque permitiría
  intentar consultar otra cuenta y no está en la especificación.
- Resolver el teléfono desde el cliente: rechazado por la misma razón y por privacidad.

## Decision 2: La billetera es propiedad del módulo wallet

**Decision**: Reutilizar `wallets` y el modelo `Wallet` ya creados por HU-08 en la
migración `0002_wallet_tables`. HU-05 solo consulta esa billetera; no crea una fila
faltante como efecto lateral.

**Rationale**: La arquitectura asigna HU-05 y la tabla `wallets` a `wallet`; HU-08 ya
implementó esa decisión y `wallet.service.create_wallet(user_id)` queda disponible para
HU-01. Preserva el flujo alternativo de HU-05 CA-5: una cuenta sin billetera debe recibir
un error, no un saldo inventado.

**Alternatives considered**:

- Crear una billetera automáticamente al consultar: rechazado porque convierte una
  lectura en escritura y contradice CA-5.
- Almacenar el saldo en `users`: rechazado porque contradice el modelo de datos y la
  responsabilidad del módulo `wallet`.

## Decision 3: Contrato de saldo, billetera ausente y sesión inválida

**Decision**: El éxito devuelve `200 {"balance": "0.00"}` con el monto como cadena
decimal de dos lugares. Una billetera ausente devuelve `404` con problema RFC 9457 y
`code` estable `wallet_not_found`. Las rutas privadas devuelven el código canónico
`unauthenticated` ante una sesión ausente, vencida o revocada, y el cliente redirige al
login para cualquier `401` privado.

**Rationale**: La respuesta de saldo y `wallet_not_found` están fijadas por
`.claude/rules/api-design.md`. Esa regla también fija `unauthenticated` para una sesión
inválida; la implementación actual de HU-02 usa `invalid_session` y el cliente ya
reacciona a ese código. La normalización debe actualizar ambos lados y sus pruebas en la
misma tarea antes de depender de ello en la pantalla de saldo.

**Alternatives considered**:

- Devolver un saldo numérico o `float`: rechazado por RNF-04.3 y la constitución.
- Devolver `200` con saldo cero si falta la billetera: rechazado porque es falso y no
  satisface HU-05 CA-5.
- Mantener códigos de sesión distintos por historia: rechazado porque rompe el contrato
  HTTP común y deja al cliente sin una reacción fiable ante un `401`.

## Decision 4: Pantalla principal como consulta de saldo

**Decision**: La ruta principal autenticada muestra `BalancePage`; después de login
válido se navega a ella. La feature obtiene el saldo a través de `shared/api/client.ts`
y presenta carga, saldo disponible y error accesible.

**Rationale**: RF-03 indica que el usuario abre la pantalla principal para consultar el
saldo; la rama actual todavía muestra una página provisional de health check.

**Alternatives considered**:

- Mantener health como pantalla principal y ocultar saldo en una ruta no enlazada:
  rechazado porque no entrega una experiencia de consulta principal.
- Llamar `fetch` desde el componente: rechazado por la regla de webapp; la feature debe
  usar `wallet/api.ts` y el cliente compartido.

## Decision 5: Rendimiento se verifica con carga, no con temporizadores de UI

**Decision**: Añadir y activar el escenario autenticado de consulta de saldo en la prueba
de carga existente, junto al escenario de recarga ya incorporado por HU-08, y comprobar
p95 <= 2 s con 20 usuarios concurrentes. Las pruebas unitarias y E2E validan
comportamiento, no latencia representativa.

**Rationale**: HU-05 CA-6 y RNF-02.1/.4 definen una métrica de sistema bajo carga. La
regla de pruebas ubica Locust en `api/tests/load/locustfile.py` y el job nocturno.

