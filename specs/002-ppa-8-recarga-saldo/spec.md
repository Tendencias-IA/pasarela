# Feature Specification: Recarga simulada de saldo (HU-08)

**Feature Branch**: `feat/PPA-8-recarga-saldo`

**Created**: 2026-10-14

**Status**: Draft

**Input**: User description: "HU-08 Realizar una recarga simulada (Jira PPA-8). Como usuario autenticado, quiero acreditar saldo ficticio en mi billetera, para disponer de dinero dentro del prototipo."

**Fuente**: `docs/referencia/requisitos-billetera-v1.0.md`, RF-06 y HU-08. Jira: PPA-8 (épica PPA-29 "Dinero: saldo, recargas y transferencias"). Dependencia: HU-02 (sesión iniciada).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Recargar saldo con un monto válido (Priority: P1)

Un usuario con sesión iniciada abre la opción de recarga, escribe un monto entre $5.000 y
$5.000.000 COP, confirma, y ve de inmediato que la operación fue exitosa y cuál es su nuevo
saldo. No se le pide ningún dato bancario, tarjeta ni medio de pago: el dinero es ficticio.

**Why this priority**: Sin recargas la billetera siempre está en $0 y ninguna otra operación
(transferir, consultar historial) tiene sentido. Es el camino que habilita el resto del prototipo.

**Independent Test**: Con un usuario autenticado y saldo $0, recargar $50.000 y verificar que
el resultado es "exitosa", que el saldo queda en $50.000 y que aparece un movimiento de
recarga por $50.000 asociado a esa billetera.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado con saldo $0, **When** recarga $5.000 (límite inferior), **Then** la operación es exitosa, el saldo queda en $5.000 y se registra un movimiento de tipo recarga, estado exitosa, por $5.000. (HU-08 CA-1, CA-3, CA-4)
2. **Given** un usuario autenticado con saldo $4.995.000, **When** recarga $5.000.000 (límite superior), **Then** la operación es exitosa y el saldo queda en $9.995.000: no existe saldo máximo. (HU-08 CA-1, CA-7)
3. **Given** un usuario autenticado, **When** recarga $120.500,50, **Then** el saldo aumenta exactamente $120.500,50, sin redondeos ni pérdida de centavos. (RNF-04.3)
4. **Given** un usuario autenticado, **When** la recarga es exitosa, **Then** la interfaz muestra un mensaje de éxito claramente distinguible y el nuevo saldo. (HU-08 CA-9, RNF-03.4)

---

### User Story 2 - Rechazo de montos inválidos sin tocar el saldo (Priority: P1)

Un usuario intenta recargar un monto fuera de rango, vacío o que no es un número. El sistema
rechaza la solicitud, explica qué debe corregir y el saldo no cambia.

**Why this priority**: Es la mitad de la regla de negocio de RF-06; sin ella una recarga de
$1 o de texto podría corromper el saldo.

**Independent Test**: Enviar $4.999, $5.000.001, "abc" y un valor vacío; en los cuatro casos
la respuesta es "rechazada" con el motivo, y el saldo antes y después es idéntico.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado con saldo $10.000, **When** recarga $4.999, **Then** la operación es rechazada por estar fuera del rango permitido y el saldo sigue en $10.000. (HU-08 CA-2, CA-5)
2. **Given** un usuario autenticado, **When** recarga $5.000.001, **Then** la operación es rechazada por estar fuera del rango permitido. (HU-08 CA-2)
3. **Given** un usuario autenticado, **When** envía "abc", un valor vacío o un número negativo, **Then** la operación es rechazada indicando que el monto debe ser un número entre $5.000 y $5.000.000 COP, y no se registra ningún movimiento. (HU-08 CA-2, CA-5)
4. **Given** un usuario autenticado, **When** la recarga es rechazada, **Then** la interfaz muestra el motivo junto al campo de monto, visualmente distinto del mensaje de éxito. (HU-08 CA-9, RNF-03.2, RNF-03.4)

---

### User Story 3 - La misma solicitud no se acredita dos veces (Priority: P2)

Un usuario hace doble clic en "Recargar", o su navegador reintenta la solicitud por un corte
de red. El saldo aumenta una sola vez y el usuario ve un único resultado.

**Why this priority**: Protege la integridad del saldo (RNF-04.4). Es P2 solo porque depende
de que exista primero el camino exitoso.

**Independent Test**: Enviar dos veces la misma solicitud de recarga (mismo identificador de
solicitud y mismo monto) y verificar que el saldo subió una sola vez, que hay un solo
movimiento y que la segunda respuesta es idéntica a la primera.

**Acceptance Scenarios**:

1. **Given** una recarga de $20.000 ya aplicada con un identificador de solicitud X, **When** se vuelve a enviar la misma solicitud con X, **Then** el saldo no cambia, no se crea otro movimiento y la respuesta reproduce el resultado original. (HU-08 CA-6)
2. **Given** una solicitud con identificador X ya aplicada por $20.000, **When** se envía X con un monto distinto, **Then** la solicitud es rechazada por conflicto y el saldo no cambia. (HU-08 CA-6)
3. **Given** un usuario autenticado, **When** envía una recarga sin identificador de solicitud, **Then** la solicitud es rechazada antes de tocar el saldo. (HU-08 CA-6)

---

### User Story 4 - Solo el titular autenticado puede recargar su billetera (Priority: P2)

Nadie puede recargar sin sesión, ni recargar la billetera de otra persona.

**Why this priority**: RNF-01.1 y RNF-01.4; sin esto cualquier visitante podría crear dinero
en cuentas ajenas.

**Independent Test**: Sin sesión, la recarga responde "no autenticado" y ningún saldo cambia;
con sesión, la recarga siempre afecta la billetera del usuario de esa sesión, aunque la
solicitud intente indicar otra.

**Acceptance Scenarios**:

1. **Given** un visitante sin sesión, **When** intenta recargar, **Then** la operación es rechazada por falta de autenticación y no se registra movimiento. (RNF-01.1)
2. **Given** un usuario autenticado, **When** recarga, **Then** el abono se aplica únicamente a su propia billetera; la solicitud no permite elegir otra. (RNF-01.4, RNF-06.1)

---

### Edge Cases

- Montos con más de dos decimales ($5.000,005): se rechazan como inválidos; no se redondean en silencio.
- Formato de entrada con separadores ("5.000" o "5,000"): el campo acepta solo dígitos y un separador decimal; la interfaz normaliza y muestra el valor interpretado antes de confirmar.
- Veinte usuarios recargando a la vez sobre billeteras distintas: todas las recargas válidas se aplican, cada saldo refleja exactamente sus propias recargas (RNF-02.4, RNF-04.2).
- Dos recargas simultáneas del mismo usuario con identificadores distintos: ambas se aplican y el saldo final es la suma (son solicitudes distintas).
- Fallo de persistencia a mitad de la operación: no queda saldo actualizado sin movimiento ni movimiento sin saldo actualizado; el usuario ve "rechazada" y puede reintentar. (RNF-04.5)
- Sesión expirada mientras el usuario escribe el monto: al confirmar, la operación se rechaza por sesión inválida y se le pide iniciar sesión de nuevo; no se aplica nada. (HU-04 CA-2, CA-3)
- El usuario no tiene billetera asociada (dato inconsistente): la recarga se rechaza y se registra el error técnico, sin crear billetera a escondidas.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir a un usuario autenticado solicitar una recarga indicando únicamente un monto en COP. (HU-08 CA-1, CA-8)
- **FR-002**: El sistema MUST aceptar montos entre $5.000 y $5.000.000 COP, ambos inclusive, con hasta dos decimales. (HU-08 CA-1)
- **FR-003**: El sistema MUST rechazar montos no numéricos, vacíos, negativos, con más de dos decimales o fuera del rango, indicando el motivo y sin modificar el saldo ni registrar movimiento. (HU-08 CA-2, CA-5)
- **FR-004**: Una recarga válida MUST incrementar el saldo de la billetera del usuario exactamente por el monto indicado, de forma inmediata y visible en la siguiente consulta de saldo. (HU-08 CA-3)
- **FR-005**: Una recarga válida MUST quedar registrada como un movimiento de tipo "recarga" con estado "exitosa", fecha, monto y billetera, de modo que aparezca en el historial del usuario. (HU-08 CA-4)
- **FR-006**: El incremento del saldo y el registro del movimiento MUST ocurrir como una sola operación: ambos se guardan o ninguno. (RNF-04.1, RNF-04.5)
- **FR-007**: El sistema MUST aplicar cada solicitud de recarga una sola vez: toda solicitud lleva un identificador único generado por la interfaz; una repetición con el mismo identificador y los mismos datos devuelve el resultado original sin volver a acreditar, y el mismo identificador con datos distintos se rechaza. (HU-08 CA-6, RNF-04.4)
- **FR-008**: El sistema MUST NOT imponer un saldo máximo. (HU-08 CA-7)
- **FR-009**: El sistema MUST NOT solicitar ni almacenar datos bancarios, tarjetas ni medios de pago. (HU-08 CA-8)
- **FR-010**: La interfaz MUST informar si la recarga fue exitosa o rechazada, distinguiéndolo visualmente y por texto, y en caso de éxito mostrar el nuevo saldo. (HU-08 CA-9, RNF-03.4)
- **FR-011**: La interfaz MUST deshabilitar el botón de confirmar mientras la solicitud está en curso y reutilizar el mismo identificador de solicitud ante un reintento del usuario. (HU-08 CA-6)
- **FR-012**: El sistema MUST exigir sesión válida y aplicar la recarga solo a la billetera del usuario de esa sesión. (RNF-01.1, RNF-01.4)
- **FR-013**: Los montos MUST manejarse con representación decimal exacta en toda la cadena (entrada, almacenamiento, respuesta), nunca con punto flotante. (RNF-04.3)
- **FR-014**: Los registros técnicos de una recarga MUST incluir el identificador de la petición y el resultado, y MUST NOT incluir datos personales del usuario más allá de su identificador interno. (RNF-06.2, RNF-06.4)

### Key Entities *(include if feature involves data)*

- **Billetera**: saldo disponible de un usuario; una por usuario; sin tope; solo cambia por recargas y transferencias exitosas.
- **Movimiento (transacción)**: registro inmutable de una operación: tipo (recarga), estado (exitosa o rechazada), monto, billetera destino, fecha y, si fue rechazada, el motivo. Es el mismo registro que luego consulta el historial (HU-09).
- **Solicitud idempotente**: identificador único generado por la interfaz para cada intento de recarga, asociado al usuario, al contenido de la solicitud y al resultado devuelto, para reproducirlo ante repeticiones.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de las recargas con monto válido incrementa el saldo exactamente por el monto y deja un movimiento visible en el historial.
- **SC-002**: El 100 % de los montos inválidos (fuera de rango, no numéricos, vacíos, con más de dos decimales) es rechazado sin ningún cambio de saldo.
- **SC-003**: Repetir una misma solicitud 10 veces produce exactamente un incremento de saldo y un movimiento.
- **SC-004**: Con 20 usuarios recargando a la vez durante 3 minutos, el 95 % de las recargas válidas se completa en 3 segundos o menos y ningún saldo difiere de la suma de sus recargas. (HU-08 CA-10, RNF-02.3, RNF-02.4)
- **SC-005**: Un usuario completa una recarga desde la pantalla principal en no más de tres clics: abrir recarga, escribir monto, confirmar. (RNF-03.1)
- **SC-006**: El resultado (exitosa o rechazada) es visible en pantalla y anunciado a lectores de pantalla; la pantalla no presenta violaciones serias de accesibilidad. (RNF-03.6)
- **SC-007**: Los datos de recargas persisten tras reiniciar la aplicación. (RNF-05.1)

## Assumptions

- La sesión y la identificación del usuario autenticado las provee HU-02; esta historia solo exige que exista una sesión válida y no define cómo se inicia.
- La consulta del saldo en pantalla (HU-05) y el historial (HU-09) no forman parte de esta historia; la recarga devuelve el nuevo saldo en su propia respuesta para poder mostrarlo sin depender de HU-05.
- El identificador de solicitud lo genera la interfaz al mostrar el formulario de recarga, y se conserva mientras el usuario no cambie el monto; cambiar el monto genera un identificador nuevo.
- Una recarga rechazada por reglas de negocio (fuera de rango) se registra como movimiento "rechazada" con su motivo solo si la solicitud fue válida en formato y autenticación, en línea con la regla de estados del proyecto; los errores de formato no crean registro.
- El monto se expresa en pesos colombianos con hasta dos decimales, aunque en la práctica los usuarios escribirán valores enteros.
- La carga acordada para el criterio de rendimiento es la de RNF-02.4: 20 usuarios concurrentes.
