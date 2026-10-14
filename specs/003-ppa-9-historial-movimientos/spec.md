# Feature Specification: Historial de movimientos (HU-09)

**Feature Branch**: `feat/PPA-9-historial-movimientos`

**Created**: 2026-10-14

**Status**: Draft

**Input**: User description: "HU-09 Consultar el historial de movimientos (Jira PPA-9). Como usuario autenticado, quiero consultar los movimientos de mi billetera, para revisar las operaciones realizadas y recibidas."

**Fuente**: `docs/referencia/requisitos-billetera-v1.0.md`, RF-05 y HU-09. Jira: PPA-9 (épica PPA-31 "Historial de movimientos"). Dependencia: HU-02 (sesión iniciada). HU-10 (filtros) construye sobre esta historia.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver los movimientos de mi billetera, del más reciente al más antiguo (Priority: P1)

Un usuario con sesión iniciada abre "Movimientos" y ve la lista de operaciones de su
billetera: recargas, transferencias enviadas y transferencias recibidas, cada una con su
fecha, monto, tipo y estado (exitosa o rechazada). La operación más reciente aparece primero.

**Why this priority**: Es el objetivo de la historia y la única forma que tiene el usuario de
verificar que una recarga o una transferencia quedó registrada (HU-08 CA-4). Sin esto, el
resto de la historia (paginación, privacidad) no tiene qué mostrar.

**Independent Test**: Con un usuario que tiene tres recargas registradas en momentos
distintos, abrir el historial y verificar que aparecen las tres, en orden inverso de fecha,
con fecha, monto, tipo "recarga" y estado.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado con una recarga exitosa de $50.000 y una recarga rechazada de $4.999, **When** abre el historial, **Then** ve dos movimientos de tipo recarga, uno con estado exitosa y monto $50.000 y otro con estado rechazada y monto $4.999. (HU-09 CA-1, CA-2)
2. **Given** un usuario con movimientos registrados en tres momentos distintos, **When** abre el historial, **Then** el más reciente aparece de primero y el más antiguo de último. (HU-09 CA-4)
3. **Given** un usuario que envió una transferencia y recibió otra, **When** abre el historial, **Then** una aparece como "transferencia enviada" y la otra como "transferencia recibida", cada una con su monto, fecha y estado. (HU-09 CA-1, CA-2)
4. **Given** cualquier movimiento, **When** se muestra en la lista, **Then** el monto aparece con separador de miles, dos decimales y la moneda COP, y la fecha en un formato legible con hora. (HU-09 CA-2, RNF-03)

---

### User Story 2 - Solo veo mis movimientos y el otro participante aparece enmascarado (Priority: P1)

El historial muestra únicamente operaciones de la billetera del usuario de la sesión. En una
transferencia, el nombre y el teléfono de la otra persona se muestran parcialmente ocultos
(iniciales y últimos cuatro dígitos), y ese enmascaramiento viene ya hecho desde el
servidor: el navegador nunca recibe el dato completo.

**Why this priority**: Es una obligación de privacidad y seguridad (RNF-01.1, RNF-06.1) al
mismo nivel que mostrar los datos. Un historial que filtre datos ajenos es peor que ninguno.

**Independent Test**: Con dos usuarios A y B, cada uno con movimientos propios, consultar el
historial como A y verificar que no aparece ningún movimiento exclusivo de B; en la
transferencia A→B, el participante se muestra como "Mar** G****" y "***4567", y ninguna
respuesta del servidor contiene el nombre ni el teléfono completo de B.

**Acceptance Scenarios**:

1. **Given** dos usuarios con movimientos distintos, **When** uno consulta su historial, **Then** solo ve los movimientos en los que su billetera es origen o destino. (HU-09 CA-5, RNF-06.1)
2. **Given** una transferencia entre A y B, **When** A ve el movimiento, **Then** el participante B aparece con el nombre con iniciales y el teléfono con solo los últimos cuatro dígitos visibles. (HU-09 CA-3, RNF-06)
3. **Given** una recarga, **When** se muestra, **Then** no tiene otro participante y no se muestra ningún dato de terceros. (HU-09 CA-1)
4. **Given** un visitante sin sesión, **When** intenta consultar el historial, **Then** la consulta se rechaza por falta de autenticación y no se devuelve ningún movimiento. (RNF-01.1, HU-02 CA-5)
5. **Given** un usuario autenticado, **When** la solicitud intenta indicar otra billetera o usuario, **Then** el sistema ignora ese dato y responde solo con los movimientos del usuario de la sesión. (HU-09 CA-5, RNF-01.4)

---

### User Story 3 - Navegar por páginas de 20 movimientos (Priority: P2)

Cuando hay más de 20 movimientos, el historial los muestra de a 20 por página e indica en qué
página está el usuario y cuántas hay. El usuario puede avanzar y retroceder; en la primera
página no puede retroceder y en la última no puede avanzar.

**Why this priority**: Con pocos movimientos una sola página basta; la paginación cobra valor
a medida que la billetera se usa. Es P2 porque depende de que la lista base (P1) exista.

**Independent Test**: Con 45 movimientos, la primera página muestra los 20 más recientes, la
tercera muestra los 5 más antiguos, el control "siguiente" está deshabilitado en la tercera y
"anterior" en la primera; el total reportado es 45.

**Acceptance Scenarios**:

1. **Given** un usuario con 45 movimientos, **When** abre el historial, **Then** ve los 20 más recientes, el indicador "página 1 de 3" y el total de 45. (HU-09 CA-6)
2. **Given** el usuario en la página 1 de 3, **When** avanza, **Then** ve los movimientos 21 a 40 en orden descendente y puede retroceder a la página 1. (HU-09 CA-6)
3. **Given** el usuario en la página 3 de 3, **When** la ve, **Then** hay 5 movimientos y el control de avanzar está deshabilitado. (HU-09 CA-6)
4. **Given** un usuario con exactamente 20 movimientos, **When** abre el historial, **Then** hay una sola página y ningún control de navegación habilitado. (HU-09 CA-6)
5. **Given** un usuario con 45 movimientos, **When** solicita la página 9, **Then** recibe una página vacía con el total 45 y la interfaz lo lleva a la última página válida; no es un error del sistema.
6. **Given** cualquier usuario, **When** solicita una página "0", "-1" o "abc", **Then** la solicitud se rechaza como inválida indicando que la página debe ser un entero desde 1.

---

### User Story 4 - Estado vacío cuando no hay movimientos (Priority: P2)

Un usuario recién registrado abre el historial y, en lugar de una tabla vacía, ve un mensaje
que le explica que aún no tiene movimientos y cómo empezar (recargar saldo).

**Why this priority**: Es el primer contacto de todo usuario nuevo con la pantalla; sin
mensaje parece un error. Es pequeña y no bloquea a nadie.

**Independent Test**: Con un usuario sin movimientos, abrir el historial y verificar que no
hay lista, que aparece el mensaje informativo y un acceso a "Recargar saldo".

**Acceptance Scenarios**:

1. **Given** un usuario sin movimientos, **When** abre el historial, **Then** ve el mensaje "Aún no tienes movimientos" con un enlace para recargar, y ningún control de paginación. (HU-09 CA-7)
2. **Given** un usuario sin movimientos, **When** hace una recarga y vuelve al historial, **Then** el mensaje desaparece y aparece la recarga. (HU-09 CA-7, HU-08 CA-4)

---

### Edge Cases

- Un movimiento rechazado se lista con estado "rechazada" y su monto, igual que uno exitoso; se distingue visualmente (RNF-03.4). Una recarga rechazada por formato (texto, vacío) nunca se registró y por tanto no aparece (regla de estados del proyecto).
- Transferencia rechazada: aparece solo en el historial de quien la intentó (billetera origen) como "transferencia enviada, rechazada"; la billetera destino no la ve, porque nunca la recibió.
- Dos movimientos con la misma fecha y hora: el orden entre ellos es estable entre consultas (desempate por el identificador del movimiento, del mayor al menor), así ningún movimiento se repite ni desaparece al cambiar de página.
- Llega un movimiento nuevo mientras el usuario está en la página 2: al avanzar puede ver repetido el último de la página anterior. Se acepta en el prototipo; la lista se recalcula al recargar la pantalla.
- Sesión expirada al cambiar de página: la consulta se rechaza por sesión inválida y la interfaz lleva al inicio de sesión. (HU-04 CA-2)
- El usuario no tiene billetera asociada (dato inconsistente): el historial responde vacío con total 0; no se crea billetera a escondidas y se registra el error técnico.
- Un tercero sin nombre o teléfono válido (dato inconsistente): se muestra "***" sin fallar la consulta.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir a un usuario autenticado consultar los movimientos de su billetera: recargas, transferencias enviadas y transferencias recibidas, tanto exitosas como rechazadas. (HU-09 CA-1)
- **FR-002**: Cada movimiento MUST presentar fecha y hora, monto, tipo (recarga, transferencia enviada o transferencia recibida) y estado (exitosa o rechazada); un movimiento rechazado incluye además el motivo. (HU-09 CA-2)
- **FR-003**: El tipo "enviada" o "recibida" MUST derivarse de si la billetera del usuario es origen o destino de la transferencia; cada operación se registra una sola vez y se muestra a cada participante desde su punto de vista. (HU-09 CA-1)
- **FR-004**: En una transferencia, el otro participante MUST mostrarse con nombre enmascarado (iniciales) y teléfono enmascarado (últimos cuatro dígitos), y el enmascaramiento MUST ocurrir en el servidor: ninguna respuesta contiene el dato completo de un tercero. (HU-09 CA-3, RNF-06.1)
- **FR-005**: Los movimientos MUST ordenarse del más reciente al más antiguo, con desempate estable para fechas iguales. (HU-09 CA-4)
- **FR-006**: El sistema MUST devolver únicamente movimientos de la billetera del usuario de la sesión; la solicitud no permite elegir otra billetera ni otro usuario. (HU-09 CA-5, RNF-01.1, RNF-01.4)
- **FR-007**: El historial MUST entregarse en páginas de exactamente 20 movimientos, numeradas desde 1, e informar la página actual, el tamaño de página y el total de movimientos. (HU-09 CA-6)
- **FR-008**: La interfaz MUST permitir avanzar y retroceder entre páginas, deshabilitando el control que no aplica en la primera y la última página. (HU-09 CA-6)
- **FR-009**: Una página inexistente (mayor que la última) MUST responder vacía con el total correcto; una página inválida (menor que 1 o no numérica) MUST rechazarse indicando el formato esperado. (HU-09 CA-6)
- **FR-010**: Si no existen movimientos, la interfaz MUST mostrar un mensaje informativo con un acceso a recargar saldo, sin lista ni paginación. (HU-09 CA-7)
- **FR-011**: Los montos MUST manejarse con representación decimal exacta de extremo a extremo y mostrarse con separador de miles, dos decimales y moneda COP. (RNF-04.3)
- **FR-012**: Los registros técnicos de la consulta MUST incluir el identificador de la petición y la página consultada, y MUST NOT incluir nombres ni teléfonos de terceros. (RNF-06.2, RNF-06.4)
- **FR-013**: El historial MUST ser accesible desde la pantalla principal en un clic y adaptarse a escritorio y móvil. (RNF-03.1, RNF-03.5)

### Key Entities *(include if feature involves data)*

- **Movimiento (transacción)**: registro inmutable ya creado por HU-08 y HU-07: tipo (recarga o transferencia), estado (exitosa o rechazada), monto, billetera origen (solo transferencias), billetera destino, motivo de rechazo y fecha. Esta historia solo lo lee.
- **Movimiento visto por el usuario**: proyección de la transacción desde la billetera del usuario: dirección (recarga, enviada, recibida), contraparte enmascarada (solo transferencias) y los campos anteriores.
- **Página de historial**: subconjunto ordenado de 20 movimientos con número de página, tamaño y total.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de los movimientos registrados de la billetera del usuario aparece en el historial, y el 0 % de los movimientos ajenos.
- **SC-002**: Ninguna respuesta del historial contiene el nombre completo ni el teléfono completo de un tercero, verificable inspeccionando todas las respuestas en pruebas automatizadas.
- **SC-003**: Con 45 movimientos, las tres páginas suman exactamente 45 elementos distintos, sin repetidos ni faltantes, en orden descendente de fecha.
- **SC-004**: Con 20 usuarios consultando a la vez durante 3 minutos, el 95 % de las consultas del historial responde en 3 segundos o menos. (HU-09 CA-8, RNF-02.2, RNF-02.4)
- **SC-005**: Un usuario llega al historial desde la pantalla principal en un clic y cambia de página en un clic. (RNF-03.1)
- **SC-006**: La pantalla, incluida la paginación y el estado vacío, no presenta violaciones serias de accesibilidad y es operable por teclado. (RNF-03.6)
- **SC-007**: Una recarga hecha en HU-08 es visible en el historial inmediatamente después de confirmarla. (HU-08 CA-4)

## Assumptions

- La sesión y el usuario autenticado los provee HU-02 (ya en `main`); esta historia solo exige una sesión válida.
- Hoy solo existen recargas en datos reales (HU-06 y HU-07 están pendientes). Los escenarios de transferencias enviadas y recibidas se verifican con movimientos de transferencia creados directamente en los datos de prueba; cuando HU-07 entregue transferencias reales, el historial las mostrará sin cambios.
- Los filtros por fecha y tipo son HU-10 y no se incluyen; esta historia deja la consulta y la pantalla listas para recibirlos.
- El tamaño de página es fijo en 20 y no es configurable por el usuario (RF-05).
- El "estado vacío" aplica cuando el usuario no tiene ningún movimiento; una página fuera de rango con movimientos existentes no es estado vacío sino navegación inválida que la interfaz corrige llevando a la última página.
- Las fechas se muestran en la zona horaria del navegador del usuario; el servidor las entrega en UTC.
- La carga acordada para el criterio de rendimiento es la de RNF-02.4: 20 usuarios concurrentes.
- Exportar, buscar por texto y ver el detalle de un movimiento están fuera del alcance de la versión 1.0.
