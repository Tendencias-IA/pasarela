# Feature Specification: Consultar el saldo (HU-05)

**Feature Branch**: `feat/PPA-9-historial-movimientos` (rama integradora acordada por el equipo; carpeta `004-ppa-5-consultar-saldo`)

**Created**: 2026-10-14

**Status**: Draft

**Input**: User description: "HU-05 Consultar el saldo (Jira PPA-5). Como usuario autenticado, quiero consultar el saldo disponible de mi billetera, para conocer cuánto dinero puedo utilizar."

**Fuente**: `docs/referencia/requisitos-billetera-v1.0.md`, RF-03 y HU-05. Jira: PPA-5. Dependencia: HU-02 (sesión iniciada). HU-06 depende de esta historia. Las historias 1 y 2 y la investigación provienen del borrador de la rama `feat/PPA-5-consultar-el-saldo` (moagu, incompleto); se revisaron, se renumeraron a `004` y se completaron con la historia 3 (pantalla principal).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consultar el saldo propio (Priority: P1)

Como usuario autenticado con una billetera asociada, consulto el saldo disponible para
conocer el dinero que puedo utilizar. El valor es exactamente el persistido y, tras una
recarga o transferencia exitosa, la siguiente consulta ya lo refleja.

**Why this priority**: Es la funcionalidad central de HU-05 y la base de HU-06 (preparar
transferencia necesita el saldo).

**Independent Test**: Con una sesión válida y una billetera con saldo persistido conocido,
consultar el saldo y recibir exactamente ese valor en COP; recargar y volver a consultar.

**Acceptance Scenarios**:

1. **Given** un usuario con sesión válida y billetera con saldo persistido `123456.70`, **When** consulta el saldo, **Then** recibe exclusivamente el saldo de su propia billetera, `123456.70`, sin redondeos ni cálculos. (HU-05 CA-1, CA-2; RNF-04.3)
2. **Given** un usuario con billetera en `0.00`, **When** aplica una recarga exitosa de `5000.00` y vuelve a consultar, **Then** el saldo es `5000.00`, igual al valor persistido. (HU-05 CA-3; HU-08 CA-4)
3. **Given** un usuario con sesión válida, **When** altera la solicitud indicando otro usuario u otra billetera, **Then** el sistema ignora ese dato y responde solo con el saldo del usuario de la sesión; el saldo ajeno nunca sale del servidor. (HU-05 CA-4; RNF-01.4; RNF-06.1)
4. **Given** un visitante sin sesión, **When** intenta consultar el saldo, **Then** la consulta se rechaza por falta de autenticación y no se devuelve ningún saldo. (RNF-01.1; HU-02 CA-5)

---

### User Story 2 - Informar una billetera ausente (Priority: P2)

Como usuario autenticado cuya cuenta no tiene billetera asociada (dato inconsistente),
recibo el aviso de que el saldo no está disponible, y el sistema registra el error técnico
para que el equipo lo investigue.

**Why this priority**: Evita presentar un saldo inexistente como válido y cubre el flujo
alternativo de RF-03. Es P2 porque el registro (HU-01) siempre crea la billetera.

**Independent Test**: Con una sesión válida de una cuenta sin billetera, solicitar el saldo
y comprobar que el sistema informa su indisponibilidad, registra el error técnico con el
identificador del usuario y no crea una billetera ni devuelve cero.

**Acceptance Scenarios**:

1. **Given** un usuario con sesión válida y sin billetera, **When** consulta el saldo, **Then** el sistema responde "saldo no disponible" (no un saldo de cero), no crea ninguna billetera y registra un error técnico sin datos personales. (HU-05 CA-5; RF-03 flujo alternativo; RNF-06.2)
2. **Given** la misma situación, **When** el usuario abre la pantalla principal, **Then** ve el texto "Saldo no disponible" en lugar de un monto. (HU-05 CA-5; RNF-03.4)

---

### User Story 3 - Ver el saldo en la pantalla principal (Priority: P1)

Al entrar a la pantalla principal tras iniciar sesión, el usuario ve una tarjeta "Saldo
disponible" con su saldo en COP. Mientras llega el dato se indica que se está consultando;
tras una recarga hecha en la pantalla de recarga, al volver al panel el saldo ya está
actualizado.

**Why this priority**: RF-03 fija que el saldo se consulta desde la pantalla principal; sin
esta pantalla la API no tiene consumidor y RNF-03.1 (funciones principales a pocos clics)
no se cumple.

**Independent Test**: Iniciar sesión con el usuario de pruebas, ver la tarjeta con el saldo
formateado, recargar `20.000` desde `/recargar`, volver al panel y ver el saldo incrementado
en esa cantidad.

**Acceptance Scenarios**:

1. **Given** un usuario con sesión y saldo `150000.00`, **When** abre la pantalla principal, **Then** ve la tarjeta "Saldo disponible" con `$ 150.000,00`. (HU-05 CA-1, CA-2; RNF-03.1)
2. **Given** la consulta en curso, **When** se muestra la tarjeta, **Then** indica "Consultando saldo…" con un estado accesible, y nunca un cero provisional. (RNF-03.4)
3. **Given** un usuario con saldo `S`, **When** recarga `20000.00` en la pantalla de recarga y vuelve al panel, **Then** la tarjeta muestra `S + 20000.00` sin recargar la página. (HU-05 CA-3; HU-08 CA-4)
4. **Given** la sesión vencida o ausente, **When** se abre la pantalla principal, **Then** la aplicación lleva al inicio de sesión. (HU-04 CA-2; RNF-01.1)

---

### Edge Cases

- Una solicitud sin sesión válida no revela ningún saldo y exige autenticación (HU-02 CA-5, RNF-01.1).
- Una solicitud alterada (parámetros `user_id`, `wallet_id`, cabeceras) no puede seleccionar ni exponer la billetera de otra cuenta (HU-05 CA-4, RNF-06.1).
- Sin billetera asociada el sistema no sustituye el resultado por un saldo de cero ni crea la billetera a escondidas; registra el error técnico (HU-05 CA-5).
- La consulta es de solo lectura: no bloquea filas ni abre transacciones de escritura, así no interfiere con recargas o transferencias concurrentes (RNF-04).
- Un fallo de red o un error inesperado del servidor se informa como "No se pudo consultar el saldo" con opción de reintentar; nunca se muestra un valor inventado.
- El saldo puede superar los límites de una recarga (no hay saldo máximo); se muestra completo con separador de miles.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir que un usuario con sesión válida consulte el saldo disponible de la billetera asociada a su propia cuenta. (HU-05 CA-1; RF-03)
- **FR-002**: El saldo mostrado MUST coincidir con el valor persistido para esa billetera, sin cálculos ni redondeos, y expresarse en COP con dos decimales. (HU-05 CA-2; RNF-04.3)
- **FR-003**: Después de una transferencia o recarga exitosa, una nueva consulta MUST reflejar el saldo persistido actualizado; en la interfaz, la tarjeta de saldo se actualiza al volver al panel sin recargar la página. (HU-05 CA-3)
- **FR-004**: El sistema MUST determinar la cuenta consultada a partir de la sesión y MUST ignorar cualquier identificador de usuario o billetera enviado en la solicitud. (HU-05 CA-4; RNF-01.4; RNF-06.1)
- **FR-005**: Si la cuenta autenticada no tiene billetera, el sistema MUST informar que el saldo no está disponible, MUST registrar el error técnico con el identificador del usuario y sin datos personales, y MUST NOT crear la billetera ni devolver cero. (HU-05 CA-5; RNF-06.2, RNF-06.4)
- **FR-006**: El sistema MUST exigir una sesión válida para consultar un saldo. (HU-02 CA-5; RNF-01.1)
- **FR-007**: La pantalla principal MUST mostrar la tarjeta "Saldo disponible" con el saldo formateado en COP, un estado de carga accesible y el texto "Saldo no disponible" cuando no hay billetera. (RF-03 flujo principal; RNF-03.1, RNF-03.4)
- **FR-008**: La consulta MUST ser de solo lectura: no abre transacciones de escritura ni bloquea billeteras. (RNF-04)
- **FR-009**: La consulta MUST responder en 2 segundos o menos para el 95 % de las solicitudes con 20 usuarios concurrentes, verificado en la prueba de carga nocturna. (HU-05 CA-6; RNF-02.1, RNF-02.4)

### Key Entities *(include if feature involves data)*

- **Usuario autenticado**: persona cuya sesión válida determina de forma exclusiva la cuenta que puede consultar.
- **Billetera**: saldo disponible asociado a una única cuenta; puede no existir en el flujo alternativo. Ya existe desde HU-08; esta historia solo la lee.
- **Saldo**: valor decimal persistido de la billetera que refleja las operaciones exitosas.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un usuario autenticado con billetera recibe el saldo persistido de su propia billetera en el 100 % de las consultas verificadas, sin diferencia de centavos.
- **SC-002**: Una consulta posterior a una recarga exitosa muestra el saldo actualizado en el 100 % de los escenarios, tanto por API como en la pantalla principal.
- **SC-003**: Ningún escenario permite a un usuario autenticado obtener el saldo de otra cuenta mediante una solicitud alterada; sin sesión, 0 saldos devueltos.
- **SC-004**: El 95 % de las consultas de saldo responde en 2 segundos o menos con 20 usuarios concurrentes. (HU-05 CA-6; RNF-02.1)
- **SC-005**: En el 100 % de los escenarios con cuenta sin billetera, el usuario ve "Saldo no disponible", no recibe un saldo ficticio y queda un registro técnico con su identificador.
- **SC-006**: La pantalla principal con la tarjeta de saldo no presenta violaciones serias de accesibilidad en escritorio ni móvil. (RNF-03.6)
- **SC-007**: El usuario ve su saldo en la primera pantalla tras iniciar sesión, sin clics adicionales. (RNF-03.1)

## Assumptions

- HU-02 proporciona la sesión válida antes de esta funcionalidad; HU-05 depende de HU-02.
- El registro (HU-01) crea la billetera; la ausencia de billetera es un dato inconsistente que se conserva como flujo alternativo explícito.
- Las recargas y transferencias que modifican el saldo pertenecen a HU-08 y HU-07; HU-05 solo consulta el valor persistido. Hoy solo existen recargas reales; el escenario con transferencia se cubre en cuanto HU-07 exista (invalidando la misma consulta de saldo).
- La carga acordada para el criterio de rendimiento es la de RNF-02.4: 20 usuarios concurrentes.
- La tarjeta de saldo convive en la pantalla principal con los accesos a recargar y ver movimientos ya existentes.
