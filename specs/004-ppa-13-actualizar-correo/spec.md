# Feature Specification: Actualizar el correo electrónico

**Feature Branch**: `feat/PPA-13-actualizar-correo`
**Created**: 2026-10-14
**Status**: Implemented, pending review
**Input**: PPA-13 / HU-13, requisitos-billetera-v1.0.md.

## User Scenarios & Testing

### User Story 1 - Cambiar mi correo (Priority: P1)

Como usuario autenticado, quiero cambiar el correo asociado a mi cuenta,
para mantener actualizada mi información de contacto.

**Why this priority**: Permite conservar los datos de contacto de la cuenta.
**Independent Test**: Editar el correo propio, guardar y reabrir el perfil.

**Acceptance Scenarios**:

1. **CA-1**: Un correo inválido se rechaza con indicaciones de corrección.
2. **CA-2**: Un correo de otra cuenta se rechaza sin modificar el anterior.
3. **CA-3**: Un correo válido y libre persiste después de reabrir la aplicación.
4. **CA-4**: El cambio conserva teléfono, identificación, saldo e historial.
5. **CA-5**: No se envía ningún código de confirmación por correo.
6. **CA-6**: Cancelar o rechazar conserva el correo anterior.

### Edge Cases

- Guardar el mismo correo, ignorando mayúsculas y espacios externos, es válido.
- Solicitudes concurrentes no pueden asignar el mismo correo a cuentas distintas.
- Sin sesión válida no se permite editar ni consultar datos propios.
- Una solicitud de correo no puede modificar teléfono, identificación u otro usuario.

## Requirements

### Functional Requirements

- **FR-001**: Solo el titular autenticado MUST cambiar su correo.
- **FR-002**: El formato MUST seguir la misma regla de registro de HU-01.
- **FR-003**: El correo MUST ser único, normalizado sin espacios externos y en minúsculas.
- **FR-004**: Un cambio válido MUST persistir y conservar los demás datos de la cuenta.
- **FR-005**: Cancelar MUST descartar la edición sin guardar.
- **FR-006**: Un rechazo MUST conservar el valor anterior y explicar la corrección.
- **FR-007**: No se envían códigos ni se verifica la propiedad del correo.

### Key Entities

- **Cuenta**: Identidad interna estable y correo de contacto único editable.

## Success Criteria

- **SC-001**: Todo correo válido y libre guardado aparece al reabrir el perfil.
- **SC-002**: Todo rechazo o cancelación conserva los datos previamente persistidos.
- **SC-003**: Ningún cambio modifica teléfono, identificación, saldo o movimientos.

## Assumptions

- Dependencia funcional: HU-11. Se reutiliza el perfil añadido como soporte en PPA-12.
- Este PR se apila sobre `feat/PPA-12-actualizar-telefono` mientras se revisa PR #6.
- Fuera de alcance: verificación por correo, contraseña, SMS y cambios financieros.
