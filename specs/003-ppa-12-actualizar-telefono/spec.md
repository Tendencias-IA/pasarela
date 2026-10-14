# Feature Specification: Actualizar el teléfono

**Feature Branch**: `feat/PPA-12-actualizar-telefono`
**Created**: 2026-10-14
**Status**: Implemented locally — pending review
**Input**: PPA-12 / HU-12, requisitos-billetera-v1.0.md.

## User Scenarios & Testing

### User Story 1 - Cambiar mi teléfono (Priority: P1)

Como usuario autenticado, quiero cambiar el teléfono asociado a mi cuenta, para
mantener actualizado mi medio de acceso y recepción de transferencias.

**Why this priority**: El teléfono identifica la cuenta para acceder y recibir dinero.
**Independent Test**: Cambiarlo desde el perfil, volver a abrirlo e iniciar sesión
con el nuevo teléfono; el anterior debe dejar de identificar esa cuenta.

**Acceptance Scenarios**:

1. **CA-1**: Dado un formato inválido, al guardar, se rechaza y se indica la corrección.
2. **CA-2**: Dado un teléfono de otra cuenta, al guardar, se rechaza sin modificar datos.
3. **CA-3**: Dado un teléfono válido y libre, al guardar, persiste al reabrir la aplicación.
4. **CA-4**: Después del cambio, el nuevo teléfono identifica inmediatamente la misma cuenta.
5. **CA-5**: Después del cambio, el anterior deja de identificarla y queda libre para registrarse.
6. **CA-6**: Al cambiarlo, saldo, historial e identificación permanecen intactos.
7. **CA-7**: Al guardar, no se envía ningún código SMS.
8. **CA-8**: Al cancelar o rechazar la solicitud, se conserva el teléfono anterior.

### Edge Cases

- Guardar el mismo teléfono es una operación válida sin cambios.
- Dos cuentas intentan adoptar el mismo teléfono: como máximo una obtiene el cambio.
- Sin sesión o con sesión expirada, no se puede consultar ni modificar el perfil.
- No se acepta un id de usuario ni cambios de identificación o correo en la solicitud.

## Requirements

### Functional Requirements

- **FR-001**: Solo el titular autenticado MUST consultar y modificar su teléfono.
- **FR-002**: El nuevo teléfono MUST ser una cadena de diez dígitos iniciada en 3,
  reutilizando la regla confirmada de HU-01.
- **FR-003**: El teléfono MUST ser único; un rechazo MUST conservar los datos anteriores.
- **FR-004**: El cambio MUST persistir y conservar la identidad interna de la cuenta.
- **FR-005**: Login y consultas por teléfono MUST usar el nuevo valor tras guardar.
- **FR-006**: Cancelar MUST descartar la edición sin guardar.
- **FR-007**: El perfil MUST mostrar únicamente los datos propios, sin contraseña ni hash.
- **FR-008**: La operación MUST NOT cambiar identificación, correo, saldo ni historial ni enviar SMS.

### Key Entities

- **Cuenta**: Mismo identificador interno, datos personales y teléfono único actualizable.
- **Sesión**: Vinculada a la cuenta por su identidad interna, no por el teléfono.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Todo cambio válido y único queda visible al reabrir el perfil.
- **SC-002**: Todo intento inválido, duplicado o sin autorización conserva el teléfono anterior.
- **SC-003**: Tras guardar, solo el nuevo teléfono permite identificar esa cuenta.
- **SC-004**: Ningún cambio altera saldo, historial o identificación.

## Assumptions

- Dependencias: HU-01, HU-02 y HU-11. La consulta propia requerida por HU-11 se
  añade como soporte mínimo porque aún no existe en main; no se declara cerrada HU-11.
- Las transferencias aún pendientes reutilizarán la búsqueda pública de cuentas por teléfono.
- Sin verificación SMS, reautenticación adicional ni revocación automática de sesiones.

## Scope Boundaries

Incluido: consultar el perfil propio, editar/cancelar teléfono y persistir el cambio.
Excluido: editar correo, identificación, contraseña, cerrar sesión y transferir dinero.
