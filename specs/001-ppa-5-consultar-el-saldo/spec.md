# Feature Specification: Consultar el saldo

**Feature Branch**: `001-ppa-5-consultar-el-saldo`

**Created**: 2026-10-14

**Status**: Draft

**Input**: User description: "HU-05: Como usuario autenticado, quiero consultar el saldo disponible de mi billetera, para conocer cuánto dinero puedo utilizar."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consultar el saldo propio (Priority: P1)

Como usuario autenticado con una billetera asociada, consulto el saldo disponible para
conocer el dinero que puedo utilizar.

**Why this priority**: Es la funcionalidad central de HU-05 y permite al usuario tomar
decisiones sobre su dinero ficticio.

**Independent Test**: Con una sesión válida y una billetera con un saldo persistido, el
usuario consulta su saldo y recibe exactamente ese valor en COP.

**Acceptance Scenarios**:

1. **Given** un usuario con sesión válida y una billetera asociada con saldo persistido,
   **When** consulta el saldo, **Then** el sistema muestra exclusivamente el saldo de su
   propia billetera. *(HU-05 CA-1, CA-2; RF-03 CA-03.1, CA-03.2)*
2. **Given** que una transferencia o recarga exitosa actualizó el saldo persistido de la
   billetera del usuario, **When** el usuario consulta el saldo, **Then** el sistema
   muestra el saldo actualizado. *(HU-05 CA-3; RF-03 CA-03.3)*
3. **Given** un usuario con sesión válida, **When** intenta alterar la solicitud para
   consultar el saldo de otra cuenta, **Then** el sistema no entrega el saldo de esa otra
   cuenta. *(HU-05 CA-4; RF-03 CA-03.4; RNF-01.4; RNF-06.1)*

---

### User Story 2 - Informar una billetera ausente (Priority: P2)

Como usuario autenticado cuya cuenta no tiene una billetera asociada, recibo una
notificación de que el saldo no está disponible.

**Why this priority**: Evita presentar un saldo inexistente como si fuera válido y cubre
el flujo alternativo de RF-03.

**Independent Test**: Con una sesión válida de una cuenta sin billetera asociada, se
solicita el saldo y se comprueba que el sistema informa su indisponibilidad y registra el
error técnico sin exponer información sensible.

**Acceptance Scenarios**:

1. **Given** un usuario con sesión válida cuya cuenta no tiene una billetera asociada,
   **When** consulta el saldo, **Then** el sistema informa que el saldo no está
   disponible y registra el error técnico. *(HU-05 CA-5; RF-03 flujo alternativo)*

---

### Edge Cases

- Una solicitud sin una sesión válida no revela ningún saldo y exige autenticación.
  *(HU-02 CA-5; RNF-01.1)*
- Una solicitud alterada no puede seleccionar ni exponer la billetera de otra cuenta.
  *(HU-05 CA-4; RNF-06.1)*
- Cuando no existe una billetera asociada, el sistema no sustituye el resultado por un
  saldo de cero.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE permitir que un usuario con sesión válida consulte el saldo
  disponible de la billetera asociada a su propia cuenta. *(HU-05 CA-1; RF-03)*
- **FR-002**: El saldo mostrado DEBE coincidir con el valor persistido para esa billetera
  y expresarse en COP. *(HU-05 CA-2; RF-03 CA-03.2)*
- **FR-003**: Después de una transferencia o recarga exitosa, una nueva consulta DEBE
  reflejar el saldo persistido actualizado. *(HU-05 CA-3; RF-03 CA-03.3)*
- **FR-004**: El sistema DEBE determinar la cuenta consultada a partir de la sesión válida
  y NO DEBE permitir que el solicitante consulte el saldo de otra cuenta alterando la
  solicitud. *(HU-05 CA-4; RNF-01.4; RNF-06.1)*
- **FR-005**: Si la cuenta autenticada no tiene una billetera asociada, el sistema DEBE
  informar que el saldo no está disponible y registrar el error técnico sin exponer datos
  sensibles. *(HU-05 CA-5; RF-03 flujo alternativo; RNF-06.2, RNF-06.4)*
- **FR-006**: El sistema DEBE exigir una sesión válida para consultar un saldo. *(HU-02
  CA-5; RNF-01.1)*

### Key Entities *(include if feature involves data)*

- **Usuario autenticado**: Persona cuya sesión válida determina de forma exclusiva la
  cuenta que puede consultar.
- **Billetera**: Saldo disponible asociado a una única cuenta; puede no existir en el
  flujo alternativo.
- **Saldo persistido**: Valor de la billetera que refleja las operaciones exitosas y se
  conserva entre sesiones.
- **Sesión**: Evidencia de autenticación que autoriza la consulta y delimita la
  titularidad de la billetera.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un usuario autenticado con billetera recibe el saldo persistido de su propia
  billetera en el 100 % de las consultas exitosas verificadas.
- **SC-002**: Una consulta posterior a una transferencia o recarga exitosa muestra el
  saldo actualizado en el 100 % de los escenarios de prueba correspondientes.
- **SC-003**: Ningún escenario de prueba permite a un usuario autenticado obtener el saldo
  de otra cuenta mediante una solicitud alterada.
- **SC-004**: El 95 % de las consultas de saldo responde en dos segundos o menos bajo la
  carga acordada. *(HU-05 CA-6; RNF-02.1)*
- **SC-005**: En el 100 % de los escenarios con una cuenta sin billetera, el usuario es
  informado de que el saldo no está disponible y no recibe un saldo ficticio.

## Assumptions

- HU-02 proporciona una sesión válida antes de que el usuario acceda a esta
  funcionalidad; HU-05 depende de HU-02.
- El registro de una cuenta normalmente crea una billetera asociada; la ausencia de ella
  se conserva como flujo alternativo explícito de esta historia.
- Las transferencias y recargas que modifican el saldo pertenecen a sus respectivas
  historias; HU-05 únicamente consulta el valor persistido resultante.
- La carga acordada para verificar el rendimiento corresponde a 20 usuarios
  concurrentes, según RNF-02.4.

