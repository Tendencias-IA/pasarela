# Feature Specification: Registrar una cuenta

**Feature Branch**: `feat/PPA-1-registrar-cuenta`

**Created**: 2026-10-14

**Status**: Implemented — pending pull request review and CI

**Input**: HU-01 Registrar una cuenta (`PPA-1`). Como visitante, quiero registrarme con mis datos personales y una contraseña, para obtener una cuenta y una billetera digital.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Crear una cuenta y billetera (Priority: P1)

Como visitante, quiero proporcionar mis datos personales y una contraseña para obtener una cuenta con una billetera digital lista para usar.

**Why this priority**: Es la capacidad inicial del producto y habilita todas las historias que requieren una cuenta registrada.

**Independent Test**: Puede verificarse enviando el formulario con datos válidos y únicos y comprobando que exista exactamente una cuenta y una billetera asociada con saldo inicial de $0 COP.

**Acceptance Scenarios**:

1. **HU-01 CA-1 — Registro exitoso**: **Given** que un visitante completa nombre, teléfono, número de identificación, correo y contraseña con datos válidos y no registrados, **When** envía el formulario, **Then** el sistema crea exactamente una cuenta con esos datos.
2. **HU-01 CA-2 — Billetera inicial**: **Given** que la cuenta fue creada correctamente, **When** finaliza el registro, **Then** el sistema crea exactamente una billetera asociada con saldo inicial de $0 COP.
3. **HU-01 CA-3 — Datos obligatorios o inválidos**: **Given** que falta un dato obligatorio o uno de los datos no cumple su formato válido, **When** el visitante intenta registrarse, **Then** el sistema rechaza la solicitud, indica los campos que debe corregir y no crea la cuenta ni la billetera.
4. **HU-01 CA-4 — Datos únicos**: **Given** que el teléfono, correo o número de identificación ya pertenece a otra cuenta, **When** el visitante intenta registrarse, **Then** el sistema rechaza la solicitud y no crea una cuenta ni billetera adicionales.
5. **HU-01 CA-5 — Contraseña válida**: **Given** que la contraseña tiene menos de ocho caracteres o no contiene al menos una letra y un número, **When** el visitante intenta registrarse, **Then** el sistema rechaza la solicitud e indica cómo corregir la contraseña.
6. **HU-01 CA-6 — Protección de contraseña**: **Given** que el visitante utiliza una contraseña válida, **When** se crea la cuenta, **Then** la contraseña queda protegida mediante un mecanismo de hash diseñado para contraseñas y nunca se conserva ni expone en texto plano.

### Edge Cases

- Dos solicitudes concurrentes intentan registrar el mismo teléfono, correo o número de identificación: como máximo una puede crear la cuenta.
- La cuenta se crea pero falla la creación de su billetera: la operación completa debe rechazarse y no debe quedar una cuenta parcial.
- Una solicitud contiene varios campos inválidos: la respuesta identifica todos los campos que el visitante debe corregir sin revelar datos sensibles.
- La contraseña contiene espacios o caracteres no alfanuméricos: solo se aplican las reglas confirmadas de longitud mínima, presencia de una letra y presencia de un número.
- Un dato coincide con otro registro después de aplicar las reglas de comparación definidas para ese campo: la solicitud se trata como duplicada.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir que un visitante solicite el registro proporcionando nombre completo, número de teléfono, número de identificación, correo electrónico y contraseña.
- **FR-002**: El sistema MUST aceptar nombres completos de 2 a 100 caracteres formados por letras, incluidas letras con tildes y otros signos diacríticos, espacios, apóstrofos y guiones.
- **FR-003**: El sistema MUST aceptar únicamente teléfonos móviles colombianos formados por exactamente 10 dígitos y cuyo primer dígito sea `3`.
- **FR-004**: El sistema MUST exigir un número de identificación de 5 a 20 caracteres alfanuméricos, único por cuenta.
- **FR-005**: El sistema MUST aceptar únicamente correos con una estructura de dirección válida.
- **FR-006**: El sistema MUST exigir una contraseña de al menos ocho caracteres que contenga como mínimo una letra y un número.
- **FR-007**: El sistema MUST garantizar que teléfono, número de identificación y correo sean únicos por cuenta, incluso ante solicitudes concurrentes.
- **FR-008**: El sistema MUST crear la cuenta y exactamente una billetera asociada con saldo inicial de $0 COP como una única operación: ambas se crean o ninguna se conserva.
- **FR-009**: El sistema MUST rechazar solicitudes con campos ausentes o inválidos e indicar qué debe corregirse sin crear información parcial.
- **FR-010**: El sistema MUST rechazar solicitudes con teléfono, número de identificación o correo ya registrados sin crear una cuenta o billetera adicional.
- **FR-011**: El sistema MUST proteger la contraseña mediante un mecanismo de hash diseñado para contraseñas y MUST NOT almacenarla, registrarla ni devolverla en texto plano.
- **FR-012**: El registro MUST NOT enviar códigos de verificación, iniciar una sesión, recuperar contraseñas ni solicitar datos financieros reales.

### Key Entities

- **Cuenta**: Representa a la persona registrada. Conserva nombre completo, teléfono, número de identificación, correo y una representación protegida de la contraseña. Teléfono, número de identificación y correo son únicos; el número de identificación es inmutable.
- **Billetera**: Representa el saldo ficticio asociado a una cuenta. Cada cuenta tiene exactamente una billetera, creada durante el registro con saldo inicial de $0 COP.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de los registros con todos los datos válidos y únicos crea exactamente una cuenta y una billetera asociada con saldo inicial de $0 COP.
- **SC-002**: El 100 % de las solicitudes con campos ausentes, inválidos o duplicados se rechaza sin crear cuentas ni billeteras parciales.
- **SC-003**: En intentos concurrentes con el mismo teléfono, correo o número de identificación, como máximo una solicitud crea la cuenta.
- **SC-004**: En el 100 % de los rechazos por validación, el visitante puede identificar qué campos debe corregir sin que la respuesta revele contraseñas ni otros secretos.
- **SC-005**: Ninguna contraseña aceptada aparece en texto plano en información persistida, respuestas o registros técnicos.

## Assumptions

- HU-01 y PPA-1 representan la misma historia y no tienen dependencias funcionales previas.
- El visitante no necesita una sesión para registrarse y el registro no inicia una sesión; el inicio de sesión corresponde a HU-02.
- Una dirección de correo válida sigue las convenciones habituales de correo electrónico; no se exige verificación de propiedad.
- Los datos utilizados en desarrollo y pruebas son ficticios.
- La solución se ofrece como aplicación web adaptable a escritorio y móvil, de acuerdo con el alcance general del producto.
- Las comparaciones de unicidad ignoran diferencias de mayúsculas y minúsculas cuando el dato admita letras.

## Scope Boundaries

### Included

- Captura y validación de los datos obligatorios del registro.
- Creación atómica de la cuenta y su billetera con saldo inicial de $0 COP.
- Rechazo de datos inválidos o duplicados con orientación para corregirlos.
- Protección de la contraseña y de los datos personales durante el registro.

### Excluded

- Inicio o cierre de sesión.
- Códigos de verificación por SMS o correo.
- Recuperación de contraseña.
- Datos financieros reales, pagos reales o integraciones bancarias.
- Consulta o actualización posterior del perfil.
