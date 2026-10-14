# Feature Specification: Iniciar sesión

**Feature Branch**: `001-iniciar-sesion`

**Created**: 2026-10-14

**Status**: Draft

**Input**: User description: "PPA-2 Iniciar sesión. Como usuario registrado, quiero iniciar sesión con mi teléfono y contraseña, para acceder a mi billetera. Criterios de aceptación: (1) Un teléfono y una contraseña válidos permiten iniciar sesión. (2) Las credenciales incorrectas no permiten acceder. (3) El mensaje de error no revela cuál credencial es incorrecta. (4) La contraseña no aparece en mensajes de error ni registros técnicos. (5) Sin una sesión válida no se puede acceder a funciones privadas."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Iniciar sesión con credenciales correctas (Priority: P1)

Como usuario registrado, ingreso mi teléfono y contraseña y obtengo acceso a mi
billetera.

**Why this priority**: Es el camino de valor de la historia; sin él no hay nada que
entregar.

**Independent Test**: Con un usuario ya existente en la base de datos, se envía su
teléfono y contraseña correctos y se verifica que la respuesta concede una sesión activa
que permite llamar después a una función privada.

**Acceptance Scenarios**:

1. **Given** un usuario registrado con teléfono y contraseña conocidos, **When** inicia
   sesión con esos datos exactos, **Then** el sistema concede una sesión activa.
2. **Given** una sesión activa recién concedida, **When** el usuario llama a una función
   privada, **Then** el sistema la permite sin pedir credenciales de nuevo.

---

### User Story 2 - Rechazar credenciales incorrectas sin revelar cuál falló (Priority: P1)

Como usuario (registrado o no), si escribo mal el teléfono o la contraseña, el sistema
me niega el acceso con un mensaje que no distingue cuál de los dos fue el error.

**Why this priority**: Es la mitad de seguridad de la historia (CA-2, CA-3); sin ella el
login "funciona" pero filtra qué teléfonos existen, lo que vulnera RNF-01.5.

**Independent Test**: Se intenta iniciar sesión con un teléfono que no existe y, por
separado, con un teléfono que existe pero contraseña incorrecta; en ambos casos se
verifica el mismo código y mensaje de error, y que ninguno de los dos crea una sesión.

**Acceptance Scenarios**:

1. **Given** un teléfono que no corresponde a ninguna cuenta, **When** se intenta
   iniciar sesión con cualquier contraseña, **Then** el sistema niega el acceso con un
   mensaje de error genérico y no concede sesión.
2. **Given** un teléfono de una cuenta existente, **When** se intenta iniciar sesión con
   una contraseña incorrecta, **Then** el sistema niega el acceso con el mismo mensaje
   de error genérico que el caso anterior y no concede sesión.
3. **Given** cualquiera de los dos casos anteriores, **When** se compara el mensaje de
   error devuelto, **Then** el mensaje es idéntico en ambos casos: no se puede inferir
   si el teléfono existe o no a partir de la respuesta.

---

### User Story 3 - Impedir el acceso a funciones privadas sin sesión válida (Priority: P1)

Como visitante sin sesión, o con una sesión que ya no es válida, no puedo usar ninguna
función privada de la billetera.

**Why this priority**: Es el propósito final de "iniciar sesión": que exista una puerta
real. Sin esta historia, el login sería una pantalla sin efecto.

**Independent Test**: Se llama a una función privada sin ninguna sesión y se verifica
que el sistema la rechaza; se repite con una sesión que ha expirado.

**Acceptance Scenarios**:

1. **Given** no existe ninguna sesión, **When** se solicita una función privada,
   **Then** el sistema la rechaza y no la ejecuta.
2. **Given** existía una sesión pero ya no es válida, **When** se solicita una función
   privada, **Then** el sistema la rechaza igual que si no existiera sesión.

---

### Edge Cases

- El usuario deja el teléfono o la contraseña vacíos: se trata como credenciales
  inválidas con el mismo mensaje genérico, sin distinguir "falta el dato" de
  "el dato es incorrecto".
- Un mismo teléfono recibe muchos intentos fallidos seguidos: por RNF-01 el sistema
  limita la tasa de intentos (ver `.claude/rules/security.md`); ese límite protege esta
  historia pero se especifica y prueba en su propia tarea de seguridad, no es un nuevo
  criterio de negocio de HU-02.
- Un usuario con sesión activa intenta "iniciar sesión" de nuevo: el sistema simplemente
  concede una nueva sesión válida; no es un error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE conceder una sesión activa cuando el teléfono y la
  contraseña enviados coinciden con los de una cuenta existente.
- **FR-002**: El sistema DEBE negar el acceso cuando el teléfono no corresponde a
  ninguna cuenta o cuando la contraseña no coincide con la de la cuenta de ese teléfono.
- **FR-003**: El sistema DEBE devolver el mismo código y el mismo mensaje de error para
  "teléfono inexistente" y para "contraseña incorrecta", de modo que la respuesta nunca
  permita distinguir cuál de los dos fue el problema.
- **FR-004**: El sistema NUNCA DEBE incluir la contraseña, en texto plano o en cualquier
  forma derivada, en un mensaje de error ni en un registro técnico, sea el intento
  exitoso o no.
- **FR-005**: El sistema DEBE impedir el acceso a cualquier función privada cuando no
  hay una sesión activa y válida asociada a la solicitud.
- **FR-006**: El sistema DEBE tratar una sesión revocada o expirada exactamente igual
  que la ausencia de sesión al evaluar el acceso a una función privada, sin distinguir
  una de la otra en la respuesta. El cierre de sesión explícito bajo pedido del usuario
  (`POST /auth/logout`) es HU-03/HU-04 y no se implementa en esta historia; aquí se
  prueba con una sesión ya revocada directamente en los datos de la prueba.

### Key Entities

- **Credenciales de inicio de sesión**: teléfono y contraseña que el usuario envía para
  autenticarse; no se persisten, solo se validan contra la cuenta existente.
- **Sesión**: estado que el sistema asocia a un usuario autenticado tras un inicio de
  sesión exitoso; determina si una solicitud posterior puede usar funciones privadas.
  Su ciclo de vida completo (expiración por inactividad, cierre explícito) se detalla en
  HU-03 y HU-04; esta historia solo crea la sesión y la usa como puerta de acceso.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de los intentos de inicio de sesión con teléfono y contraseña
  correctos conceden acceso a la billetera.
- **SC-002**: El 100% de los intentos con teléfono o contraseña incorrectos son
  rechazados con el mismo mensaje, sin excepción.
- **SC-003**: El 0% de los mensajes de error o registros técnicos generados durante el
  inicio de sesión contiene la contraseña enviada.
- **SC-004**: El 100% de las solicitudes a una función privada sin sesión válida son
  rechazadas sin ejecutar la función.

## Assumptions

- Las cuentas de usuario (teléfono, contraseña con hash) ya existen en el sistema antes
  de esta historia; su creación es HU-01 y queda fuera de este alcance. Para probar y
  demostrar HU-02 se usan cuentas creadas directamente en la base de datos de pruebas
  (factories), no a través de un flujo de registro.
- "Función privada" es cualquier operación que requiera saber quién es el usuario (por
  ejemplo, ver su saldo o su perfil); esta historia no implementa ninguna de esas
  funciones, solo el mecanismo que las protege a todas por igual.
- El cierre de sesión explícito (`POST /auth/logout`) y la expiración deslizante de 5
  minutos se especifican con su propio detalle en HU-03 y HU-04 y no se implementan
  aquí; esta historia solo exige que una sesión sin validez (ausente, revocada o
  vencida) bloquee el acceso igual en los tres casos.
- No hay "recordar sesión" ni inicio de sesión por un medio distinto a teléfono y
  contraseña (sin SSO, sin verificación por SMS o correo), según el alcance fijo del
  prototipo.
