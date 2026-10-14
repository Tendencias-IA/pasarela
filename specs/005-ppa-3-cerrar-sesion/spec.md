# Feature Specification: Cerrar sesión

**Feature Branch**: `feat/PPA-3-cerrar-sesion`
**Created**: 2026-10-14
**Status**: Ready for implementation
**Input**: PPA-3 / HU-03, requisitos-billetera-v1.0.md, CA-1 a CA-4.

## User Scenarios & Testing

### User Story 1 - Cerrar el acceso a mi cuenta (Priority: P1)

Como usuario autenticado, quiero cerrar mi sesión para impedir que otra persona
continúe utilizando mi cuenta.

**Why this priority**: Protege una cuenta abierta en un dispositivo compartido.
**Independent Test**: Iniciar sesión, cerrarla y repetir una petición privada
con la sesión anterior: se exige iniciar sesión nuevamente.

**Acceptance Scenarios**:

1. CA-1: Dada una sesión activa, al seleccionar Cerrar sesión, queda invalidada.
2. CA-2: Después del cierre, acceder a una función privada exige iniciar sesión.
3. CA-3: Volver atrás, recargar o repetir una petición con la sesión anterior
   no recupera acceso ni datos privados.
4. CA-4: El cierre no modifica saldo, movimientos ni datos personales.

### Edge Cases

- Sin sesión, vencida o ya revocada: se rechaza el acceso y se muestra el login.
- Un fallo de red o del servidor no se presenta como cierre exitoso; permite reintentar.
- Pulsaciones repetidas no generan solicitudes simultáneas.
- Solo se cierra la sesión activa; no se cierran otras sesiones del usuario.

## Requirements

### Functional Requirements

- FR-001: Invalidar la sesión activa en el servidor (HU-03 CA-1, RNF-01.3).
- FR-002: Exigir nueva autenticación para funciones privadas (HU-03 CA-2).
- FR-003: Eliminar datos privados locales y negar reutilización (HU-03 CA-3).
- FR-004: No escribir datos de cuenta ni operaciones financieras (HU-03 CA-4).
- FR-005: Permitir reintentar un cierre fallido sin afirmar éxito.

### Key Entities

- Sesión: autorización temporal de una cuenta; activa, vencida o revocada.
- Cuenta y billetera: datos que permanecen intactos tras el cierre.

## Success Criteria

### Measurable Outcomes

- SC-001: Los cuatro criterios de aceptación pasan pruebas automáticas.
- SC-002: Ninguna petición con la sesión revocada permite una función privada.
- SC-003: Cierre accesible en móvil y escritorio en no más de dos acciones.
- SC-004: Cero cambios en datos personales, saldo o movimientos por el cierre.

## Assumptions

- Dependencia HU-02 ya disponible en main; no depende de PPA-12/PPA-13.
- Se reutiliza la expiración existente; no se implementa el temporizador de HU-04.
- No hay cierre global de todas las sesiones ni confirmación adicional.
- Se requieren pruebas primero, integración real y escenarios de navegador.
