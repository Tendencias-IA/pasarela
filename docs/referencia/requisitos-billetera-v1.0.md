
Especificación de Requisitos e Historias de Usuario de la Billetera Digital
Documento centralizado del prototipo académico
Versión 1.0  |  Octubre de 2026
Propósito
Este documento reúne el alcance funcional, los requisitos de calidad, las reglas de negocio confirmadas y las historias de usuario de la billetera digital. Su objetivo es mantener una única referencia para análisis, diseño, desarrollo y pruebas.
Alcance
La solución es una aplicación web responsive para fines académicos. Utiliza dinero y datos ficticios, no procesa pagos reales, no envía códigos de verificación y no incluye recuperación de contraseña.

Organización del documento
Alcance y reglas confirmadas
Requisitos funcionales
Requisitos no funcionales
Trazabilidad entre requisitos e historias
Historias de usuario y criterios de aceptación
Alcance y reglas confirmadas
Teléfono, número de identificación y correo electrónico son únicos por cuenta.
El teléfono se utiliza para iniciar sesión y para identificar al destinatario de una transferencia.
El teléfono y el correo pueden modificarse; el número de identificación permanece inmutable.
Al cambiar el teléfono, el anterior queda disponible para otro registro.
No se envían códigos de verificación por SMS o correo.
Las transferencias admiten valores entre $100 y $3.000.000 COP, inclusive.
Las recargas admiten valores entre $5.000 y $5.000.000 COP, inclusive.
La billetera no tiene saldo máximo.
El historial muestra 20 movimientos por página y permite filtrar por rango de fechas y tipo.
Los tipos de filtro son todas, transferencias enviadas, transferencias recibidas y recargas.
Las operaciones solo utilizan los estados exitosa y rechazada.
La sesión expira después de cinco minutos sin actividad.
La aplicación es exclusivamente web y se adapta a escritorio y móvil.

Requisitos funcionales
Los requisitos funcionales describen las acciones disponibles para visitantes y usuarios autenticados. Las aclaraciones confirmadas durante el análisis se incorporan directamente en sus reglas y criterios.
Código
Módulo
Funcionalidad
Prioridad
RF-01
Usuarios
Registro de usuarios
Alta
RF-02
Acceso
Inicio y cierre de sesión
Alta
RF-03
Billetera
Consulta de saldo
Alta
RF-04
Transferencias
Transferencias entre usuarios
Alta
RF-05
Movimientos
Historial de movimientos
Media
RF-06
Recargas
Recarga simulada de saldo
Alta
RF-07
Perfil
Gestión del perfil
Media

RF-01  Registro de usuarios
Prioridad  Alta
Actor principal  Visitante no autenticado
Descripción  El sistema permite crear una cuenta con nombre completo, teléfono, número de identificación, correo electrónico y contraseña. Al completar el registro, crea una billetera con saldo inicial de $0 COP.
Precondiciones
El visitante no necesita una sesión iniciada.
El formulario de registro se encuentra disponible.
Flujo principal
1. El visitante abre la opción de registro.
2. El sistema solicita los datos obligatorios.
3. El visitante completa y envía el formulario.
4. El sistema valida los formatos, la contraseña y la unicidad del teléfono, la identificación y el correo.
5. El sistema crea la cuenta y la billetera con saldo inicial de $0 COP.
6. El sistema confirma el registro.
Flujos alternativos
Si falta un dato o su formato es inválido, el sistema identifica el campo que debe corregirse.
Si el teléfono, la identificación o el correo ya está registrado, el sistema rechaza la solicitud.
Criterios de aceptación
CA-01.1 El usuario puede registrarse con datos válidos.
CA-01.2 El sistema rechaza registros que incumplen las validaciones.
CA-01.3 Teléfono, identificación y correo no pueden repetirse entre cuentas.
CA-01.4 La contraseña contiene al menos ocho caracteres, una letra y un número.
CA-01.5 La cuenta creada dispone de una billetera con saldo inicial de $0 COP.

RF-02  Inicio y cierre de sesión
Prioridad  Alta
Actor principal  Usuario registrado
Descripción  El sistema permite iniciar sesión mediante teléfono y contraseña, cerrar la sesión de forma voluntaria y finalizarla automáticamente después de cinco minutos de inactividad.
Precondiciones
El usuario tiene una cuenta registrada.
Flujo principal
1. El usuario ingresa su teléfono y contraseña.
2. El sistema valida las credenciales.
3. El sistema habilita las funciones privadas.
4. El usuario puede cerrar la sesión desde la interfaz.
5. El sistema invalida la sesión al cerrar o después de cinco minutos sin actividad.
Flujos alternativos
Si las credenciales son incorrectas, el sistema rechaza el acceso sin revelar cuál credencial falló.
Si no existe una sesión válida, el sistema impide acceder a funciones privadas.
Criterios de aceptación
CA-02.1 Las credenciales válidas permiten iniciar sesión.
CA-02.2 Las credenciales inválidas no permiten acceder.
CA-02.3 El cierre voluntario invalida la sesión.
CA-02.4 La sesión expira después de cinco minutos de inactividad.
CA-02.5 Un usuario no autenticado no puede consultar saldos ni ejecutar transacciones.

RF-03  Consulta de saldo
Prioridad  Alta
Actor principal  Usuario autenticado
Descripción  El sistema permite consultar el saldo disponible de la billetera asociada al usuario autenticado.
Precondiciones
El usuario tiene una sesión válida.
La cuenta tiene una billetera asociada.
Flujo principal
1. El usuario abre la pantalla principal.
2. El sistema consulta el saldo persistido.
3. El sistema muestra el saldo disponible en COP.
Flujos alternativos
Si no se encuentra una billetera asociada, el sistema informa que el saldo no está disponible y registra el error técnico.
Criterios de aceptación
CA-03.1 El sistema muestra el saldo del usuario autenticado.
CA-03.2 El saldo mostrado coincide con el saldo persistido.
CA-03.3 El saldo refleja las transferencias y recargas exitosas.
CA-03.4 El usuario no puede consultar el saldo de otra cuenta.

RF-04  Transferencias entre usuarios
Prioridad  Alta
Actor principal  Usuario autenticado
Descripción  El sistema permite enviar dinero ficticio a otro usuario registrado. El destinatario se identifica mediante su número de teléfono.
Precondiciones
El emisor tiene una sesión válida.
El destinatario tiene una cuenta y billetera asociadas.
El emisor dispone de saldo suficiente.
Flujo principal
1. El usuario abre la opción de transferencias.
2. Ingresa el teléfono del destinatario y un monto entre $100 y $3.000.000 COP.
3. El sistema valida el destinatario, el monto y el saldo disponible.
4. El sistema presenta el monto y datos parcialmente ocultos del destinatario.
5. El usuario confirma la transferencia.
6. El sistema actualiza ambos saldos como una única operación lógica.
7. El sistema registra la transferencia y muestra el resultado.
Flujos alternativos
Si el destinatario no existe o es la propia cuenta, el sistema rechaza la operación.
Si el monto está fuera de los límites o el saldo es insuficiente, el sistema no ejecuta la transferencia.
Si ocurre un error, el sistema no deja una transferencia aplicada parcialmente.
Criterios de aceptación
CA-04.1 El destinatario se identifica mediante su teléfono.
CA-04.2 El usuario revisa el destinatario parcialmente oculto y el monto antes de confirmar.
CA-04.3 Los límites de $100 y $3.000.000 COP son inclusivos.
CA-04.4 Una operación exitosa actualiza ambos saldos y queda registrada.
CA-04.5 Una operación rechazada no modifica los saldos.
CA-04.6 Una solicitud no puede aplicar la transferencia más de una vez.

RF-05  Historial de movimientos
Prioridad  Media
Actor principal  Usuario autenticado
Descripción  El sistema permite consultar transferencias enviadas, transferencias recibidas y recargas asociadas a la billetera del usuario.
Precondiciones
El usuario tiene una sesión válida.
La cuenta tiene una billetera asociada.
Flujo principal
1. El usuario abre el historial.
2. El sistema recupera los movimientos de su billetera.
3. El sistema muestra 20 movimientos por página, del más reciente al más antiguo.
4. El usuario puede filtrar por rango de fechas y tipo de movimiento.
Flujos alternativos
Si no existen movimientos o coincidencias para los filtros, el sistema muestra un estado vacío.
Criterios de aceptación
CA-05.1 El historial incluye transferencias enviadas, recibidas y recargas.
CA-05.2 Cada movimiento muestra fecha, monto, tipo y estado.
CA-05.3 Los datos del otro participante aparecen parcialmente ocultos.
CA-05.4 El usuario solo consulta movimientos de su billetera.
CA-05.5 La paginación muestra 20 registros por página.
CA-05.6 Los filtros de fecha y tipo pueden combinarse.

RF-06  Recarga simulada de saldo
Prioridad  Alta
Actor principal  Usuario autenticado
Descripción  El sistema permite acreditar inmediatamente un monto ficticio en la billetera. No intervienen bancos, tarjetas ni medios de pago reales.
Precondiciones
El usuario tiene una sesión válida.
La cuenta tiene una billetera asociada.
Flujo principal
1. El usuario abre la opción de recarga.
2. Ingresa un monto entre $5.000 y $5.000.000 COP.
3. El sistema valida el monto.
4. El sistema acredita el saldo y registra la recarga.
5. El sistema muestra el resultado y el saldo actualizado.
Flujos alternativos
Si el monto está fuera de los límites o es inválido, el sistema rechaza la solicitud sin modificar el saldo.
Criterios de aceptación
CA-06.1 Los límites de $5.000 y $5.000.000 COP son inclusivos.
CA-06.2 Una recarga válida incrementa inmediatamente el saldo.
CA-06.3 Una recarga inválida no modifica el saldo.
CA-06.4 Una recarga exitosa queda registrada.
CA-06.5 La billetera no tiene saldo máximo.
CA-06.6 Una solicitud no puede acreditar el monto más de una vez.

RF-07  Gestión del perfil
Prioridad  Media
Actor principal  Usuario autenticado
Descripción  El sistema permite consultar el nombre completo, el teléfono, el número de identificación y el correo. El usuario puede modificar únicamente el teléfono y el correo.
Precondiciones
El usuario tiene una sesión válida.
La cuenta se encuentra registrada.
Flujo principal
1. El usuario abre su perfil.
2. El sistema muestra sus datos personales.
3. El usuario modifica el teléfono o el correo.
4. El sistema valida el formato y la unicidad del nuevo valor.
5. El sistema guarda los cambios válidos.
Flujos alternativos
Si el dato es inválido o ya pertenece a otra cuenta, el sistema rechaza el cambio.
Si el usuario cancela la edición, el sistema conserva los datos anteriores.
Criterios de aceptación
CA-07.1 El usuario consulta su propio perfil.
CA-07.2 El número de identificación es inmutable.
CA-07.3 El teléfono y el correo pueden actualizarse sin códigos de verificación.
CA-07.4 El nuevo teléfono se usa inmediatamente para iniciar sesión y recibir transferencias.
CA-07.5 El teléfono anterior queda disponible para otro registro.
CA-07.6 Los cambios válidos persisten entre sesiones.

Requisitos no funcionales
Estos requisitos definen las condiciones de seguridad, rendimiento, usabilidad, integridad, persistencia y privacidad que deben cumplir las funciones de la aplicación.
Código
Categoría
Objetivo
RNF-01
Seguridad
Impedir el acceso no autorizado a cuentas y operaciones.
RNF-02
Rendimiento
Mantener tiempos de respuesta medibles bajo la carga de prueba acordada.
RNF-03
Usabilidad y accesibilidad
Permitir que el usuario complete las tareas principales sin asistencia técnica.
RNF-04
Fiabilidad e integridad
Mantener la consistencia de los saldos y las transacciones.
RNF-05
Persistencia
Evitar la pérdida de información entre sesiones o ante fallos recuperables.
RNF-06
Privacidad
Limitar el uso y la exposición de los datos personales.
RNF-01  Seguridad
Objetivo  Impedir el acceso no autorizado a cuentas y operaciones.
RNF-01.1 Se exige autenticación para consultar saldos, modificar perfiles y realizar transacciones.
RNF-01.2 Las contraseñas se almacenan mediante un algoritmo de hash diseñado para contraseñas.
RNF-01.3 Las sesiones se invalidan al cerrar sesión o después de cinco minutos de inactividad.
RNF-01.4 El servidor valida permisos, montos y titularidad, sin depender de las validaciones del cliente.
RNF-01.5 Los errores de autenticación no revelan contraseñas ni otros datos sensibles.
Verificación  Ejecutar pruebas sin autenticación, intentos de acceso a otra billetera, validaciones de permisos y revisión del almacenamiento de credenciales.
RNF-02  Rendimiento
Objetivo  Mantener tiempos de respuesta medibles bajo la carga de prueba acordada.
RNF-02.1 El 95 % de las consultas de saldo responde en un máximo de dos segundos.
RNF-02.2 El 95 % de las consultas del historial responde en un máximo de tres segundos.
RNF-02.3 El 95 % de las transferencias y recargas válidas se completa en un máximo de tres segundos.
RNF-02.4 El sistema soporta al menos 20 usuarios concurrentes sin perder la integridad de los saldos.
Verificación  Ejecutar pruebas de carga y medir tiempos, solicitudes satisfactorias y consistencia de las transacciones.
RNF-03  Usabilidad y accesibilidad
Objetivo  Permitir que el usuario complete las tareas principales sin asistencia técnica.
RNF-03.1 Las funciones principales se alcanzan en no más de tres clics.
RNF-03.2 Los formularios identifican campos obligatorios y explican cómo corregir errores.
RNF-03.3 Antes de confirmar una transferencia se muestran el destinatario parcialmente oculto y el monto.
RNF-03.4 La interfaz distingue visualmente las operaciones exitosas y rechazadas.
RNF-03.5 La interfaz web se adapta a pantallas de escritorio y móviles.
RNF-03.6 Los controles tienen etiquetas comprensibles y la navegación básica funciona mediante teclado.
Verificación  Realizar pruebas de tareas, revisar distintos tamaños de pantalla y comprobar la navegación mediante teclado.
RNF-04  Fiabilidad e integridad
Objetivo  Mantener la consistencia de los saldos y las transacciones.
RNF-04.1 Las transferencias son atómicas: ambos saldos se actualizan o ninguno cambia.
RNF-04.2 Las operaciones simultáneas no generan saldos incorrectos ni permiten gastar más dinero del disponible.
RNF-04.3 Los montos usan una representación decimal exacta apropiada para valores monetarios.
RNF-04.4 Una misma solicitud de transferencia o recarga no puede aplicarse dos veces.
RNF-04.5 Una operación fallida no se presenta como exitosa.
Verificación  Ejecutar pruebas de concurrencia, provocar fallos y comprobar que saldos y registros permanecen consistentes.
RNF-05  Persistencia
Objetivo  Evitar la pérdida de información entre sesiones o ante fallos recuperables.
RNF-05.1 Los usuarios, perfiles, saldos y transacciones se conservan al cerrar y volver a abrir la aplicación.
RNF-05.2 Las transacciones confirmadas se persisten de acuerdo con las garantías de la base de datos.
Verificación  Reiniciar la aplicación y comprobar que los datos persisten.
RNF-06  Privacidad
Objetivo  Limitar el uso y la exposición de los datos personales.
RNF-06.1 Cada usuario solo ve los datos personales y movimientos que está autorizado a consultar.
RNF-06.2 Las contraseñas y otros secretos no aparecen en registros ni mensajes de error.
RNF-06.3 Los datos de prueba son ficticios y no incluyen información financiera real.
RNF-06.4 Los registros técnicos evitan exponer teléfonos completos y otros datos personales innecesarios.
Verificación  Revisar permisos, registros de aplicación y datos usados en el entorno de pruebas.

Trazabilidad entre requisitos e historias
La matriz muestra qué historias implementan cada requisito funcional. Los requisitos no funcionales se verifican de forma transversal en las historias que procesan o exponen la información correspondiente.
Requisito
Funcionalidad
Historias
RF-01
Registro de usuarios
HU-01
RF-02
Inicio y cierre de sesión
HU-02, HU-03 y HU-04
RF-03
Consulta de saldo
HU-05
RF-04
Transferencias entre usuarios
HU-06 y HU-07
RF-05
Historial de movimientos
HU-09 y HU-10
RF-06
Recarga simulada
HU-08
RF-07
Gestión del perfil
HU-11, HU-12 y HU-13
Aplicación de los requisitos no funcionales
Requisito
Historias relacionadas
RNF-01
Todas las historias con acceso autenticado; énfasis en HU-01 a HU-07 y HU-11 a HU-13
RNF-02
HU-05, HU-07, HU-08, HU-09 y HU-10
RNF-03
Todas las historias con interfaz web
RNF-04
HU-05, HU-07, HU-08 y HU-09
RNF-05
HU-01, HU-05, HU-07, HU-08, HU-09, HU-12 y HU-13
RNF-06
Todas las historias; énfasis en HU-02, HU-06, HU-09, HU-11, HU-12 y HU-13

Historias de usuario
Las historias siguientes dividen los requisitos funcionales en entregables verificables. Cada historia incluye prioridad, dependencias y criterios de aceptación propios.

HU-01  Registrar una cuenta
Como visitante, quiero registrarme con mis datos personales y una contraseña, para obtener una cuenta y una billetera digital.
Prioridad
Alta
Dependencias
Ninguna

Datos obligatorios
Nombre completo
Número de teléfono
Número de identificación
Correo electrónico
Contraseña
Criterios de aceptación
1. Dado que completo todos los campos con datos válidos y no registrados, cuando envío el formulario, entonces el sistema crea mi cuenta.
2. Al crear la cuenta, el sistema crea una billetera asociada con saldo inicial de $0 COP.
3. Si falta un campo obligatorio o contiene un valor inválido, el sistema rechaza la solicitud e indica qué debe corregirse.
4. Si el teléfono, el correo o el número de identificación ya pertenece a otra cuenta, el sistema rechaza la solicitud sin crear una cuenta adicional.
5. La contraseña debe tener al menos ocho caracteres, una letra y un número.
6. La contraseña se almacena mediante un algoritmo de hash para contraseñas y nunca en texto plano.
Fuera de alcance. Envío de códigos de verificación y uso de datos financieros reales.

HU-02  Iniciar sesión
Como usuario registrado, quiero iniciar sesión con mi teléfono y contraseña, para acceder a mi billetera.
Prioridad
Alta
Dependencias
HU-01

Criterios de aceptación
1. Con un teléfono y una contraseña válidos, el sistema crea una sesión y permite el acceso.
2. Si el teléfono o la contraseña son incorrectos, el sistema rechaza el acceso.
3. El mensaje de autenticación no indica cuál de las credenciales es incorrecta.
4. Los mensajes de error y los registros técnicos no muestran la contraseña.
5. Un usuario sin sesión válida no puede consultar saldos, movimientos o perfiles ni realizar transferencias o recargas.

HU-03  Cerrar sesión
Como usuario autenticado, quiero cerrar mi sesión, para impedir que otra persona continúe utilizando mi cuenta.
Prioridad
Alta
Dependencias
HU-02

Criterios de aceptación
1. Cuando selecciono Cerrar sesión, el sistema invalida la sesión activa.
2. Después del cierre, cualquier acceso a una función privada exige iniciar sesión nuevamente.
3. La sesión invalidada no puede reutilizarse mediante navegación hacia atrás, recarga de página o repetición de una solicitud anterior.
4. Cerrar sesión no modifica saldos, movimientos ni datos personales.

HU-04  Cerrar una sesión por inactividad
Como usuario autenticado, quiero que mi sesión expire después de un periodo de inactividad, para proteger mi cuenta si dejo el dispositivo desatendido.
Prioridad
Alta
Dependencias
HU-02

Criterios de aceptación
1. Después de cinco minutos sin actividad, el sistema invalida la sesión.
2. Una operación privada solicitada después de la expiración exige iniciar sesión nuevamente.
3. La expiración no confirma ni ejecuta automáticamente una operación que estuviera pendiente.
4. La actividad válida del usuario reinicia el periodo de inactividad.

HU-05  Consultar el saldo
Como usuario autenticado, quiero consultar el saldo disponible de mi billetera, para conocer cuánto dinero puedo utilizar.
Prioridad
Alta
Dependencias
HU-02

Criterios de aceptación
1. El sistema muestra exclusivamente el saldo de la billetera del usuario autenticado.
2. El saldo mostrado coincide con el valor persistido en el sistema.
3. Después de una transferencia o recarga exitosa, la consulta refleja el saldo actualizado.
4. El usuario no puede alterar la solicitud para consultar el saldo de otra cuenta.
5. Si la cuenta no tiene una billetera asociada, el sistema informa que el saldo no está disponible y registra el error técnico.
6. La consulta responde en un máximo de dos segundos para al menos el 95 % de las solicitudes bajo la carga acordada.

HU-06  Preparar una transferencia
Como usuario autenticado, quiero ingresar el teléfono del destinatario y el monto, para revisar una transferencia antes de confirmarla.
Prioridad
Alta
Dependencias
HU-02 y HU-05

Criterios de aceptación
1. El sistema permite ingresar el teléfono del destinatario y un monto en COP.
2. El monto permitido se encuentra entre $100 y $3.000.000 COP, inclusive.
3. El sistema rechaza montos no numéricos o fuera de los límites establecidos.
4. El sistema rechaza la solicitud si el teléfono no pertenece a una cuenta registrada.
5. El sistema rechaza la solicitud si el destinatario corresponde a la cuenta del emisor.
6. El sistema rechaza la solicitud si el saldo disponible es inferior al monto solicitado.
7. Cuando los datos son válidos, el sistema muestra un resumen con el monto y datos parcialmente ocultos del destinatario.
8. Preparar la transferencia no modifica saldos ni crea un movimiento financiero.

HU-07  Confirmar una transferencia
Como usuario autenticado, quiero confirmar una transferencia previamente revisada, para enviar dinero a otro usuario.
Prioridad
Alta
Dependencias
HU-06

Criterios de aceptación
1. La transferencia solamente se ejecuta después de seleccionar Confirmar.
2. Antes de procesarla, el servidor vuelve a validar la sesión, el destinatario, el monto, los límites, la titularidad y el saldo disponible.
3. Una transferencia exitosa descuenta el monto al emisor y lo acredita al destinatario.
4. Ambos saldos se actualizan como una única operación atómica: se actualizan ambos o ninguno.
5. Una transferencia exitosa queda registrada en el historial de ambos participantes.
6. Una transferencia rechazada no modifica ninguno de los saldos.
7. La interfaz informa si la operación fue exitosa o rechazada.
8. Una misma solicitud no puede aplicar la transferencia más de una vez.
9. Las operaciones simultáneas no pueden generar saldos negativos ni permitir gastar más dinero del disponible.
10. La operación se completa en un máximo de tres segundos para al menos el 95 % de los casos válidos bajo la carga acordada.

HU-08  Realizar una recarga simulada
Como usuario autenticado, quiero acreditar saldo ficticio en mi billetera, para disponer de dinero dentro del prototipo.
Prioridad
Alta
Dependencias
HU-02

Criterios de aceptación
1. El sistema permite ingresar un monto entre $5.000 y $5.000.000 COP, inclusive.
2. El sistema rechaza montos no numéricos o fuera de los límites establecidos.
3. Una recarga válida aumenta inmediatamente el saldo por el monto indicado.
4. Una recarga exitosa queda registrada en el historial.
5. Una recarga rechazada no modifica el saldo.
6. Una misma solicitud no puede acreditar el monto más de una vez.
7. La billetera no tiene un saldo máximo.
8. La recarga no solicita ni utiliza cuentas bancarias, tarjetas o medios de pago reales.
9. La interfaz informa si la operación fue exitosa o rechazada.
10. La operación se completa en un máximo de tres segundos para al menos el 95 % de los casos válidos bajo la carga acordada.

HU-09  Consultar el historial de movimientos
Como usuario autenticado, quiero consultar los movimientos de mi billetera, para revisar las operaciones realizadas y recibidas.
Prioridad
Media
Dependencias
HU-02

Criterios de aceptación
1. El historial incluye transferencias enviadas, transferencias recibidas y recargas.
2. Cada movimiento muestra fecha, monto, tipo de operación y estado.
3. En una transferencia se presenta información parcialmente oculta del otro participante.
4. Los movimientos aparecen ordenados del más reciente al más antiguo.
5. El usuario solamente puede consultar movimientos asociados a su billetera.
6. Se muestran 20 movimientos por página y se permite avanzar o retroceder cuando existen más resultados.
7. Si no existen movimientos, el sistema muestra un mensaje informativo.
8. La consulta responde en un máximo de tres segundos para al menos el 95 % de las solicitudes bajo la carga acordada.

HU-10  Filtrar el historial
Como usuario autenticado, quiero filtrar los movimientos por fecha y tipo, para encontrar operaciones específicas.
Prioridad
Media
Dependencias
HU-09

Criterios de aceptación
1. El usuario puede seleccionar un rango con fecha inicial y fecha final.
2. La fecha inicial no puede ser posterior a la fecha final.
3. El filtro de tipo ofrece: todas, transferencias enviadas, transferencias recibidas y recargas.
4. Los filtros de fecha y tipo pueden utilizarse simultáneamente.
5. Los resultados conservan el orden del más reciente al más antiguo y la paginación de 20 movimientos.
6. Cuando se modifican los filtros, la visualización regresa a la primera página.
7. Si no existen coincidencias, el sistema muestra un estado vacío sin eliminar los filtros elegidos.

HU-11  Consultar el perfil
Como usuario autenticado, quiero consultar los datos asociados a mi cuenta, para verificar que mi información sea correcta.
Prioridad
Media
Dependencias
HU-02

Criterios de aceptación
1. El perfil muestra nombre completo, teléfono, número de identificación y correo electrónico.
2. El número de identificación se presenta como un campo de solo lectura.
3. La contraseña no se muestra en el perfil.
4. El usuario solo puede consultar su propio perfil.
5. Los datos mostrados coinciden con la información persistida.

HU-12  Actualizar el teléfono
Como usuario autenticado, quiero cambiar el teléfono asociado a mi cuenta, para mantener actualizado mi medio de acceso y recepción de transferencias.
Prioridad
Media
Dependencias
HU-11

Criterios de aceptación
1. El sistema valida el formato del nuevo teléfono.
2. El cambio se rechaza si el teléfono pertenece a otra cuenta.
3. Un cambio válido se guarda y persiste después de cerrar y volver a abrir la aplicación.
4. El nuevo teléfono se convierte inmediatamente en el identificador para iniciar sesión y recibir transferencias.
5. El teléfono anterior deja de identificar la cuenta y queda disponible para otro registro.
6. El cambio no modifica el saldo, el historial ni el número de identificación.
7. No se envían códigos de confirmación por SMS.
8. Si el usuario cancela la edición o el cambio es rechazado, se conserva el teléfono anterior.

HU-13  Actualizar el correo electrónico
Como usuario autenticado, quiero cambiar el correo asociado a mi cuenta, para mantener actualizada mi información de contacto.
Prioridad
Media
Dependencias
HU-11

Criterios de aceptación
1. El sistema valida el formato del nuevo correo.
2. El cambio se rechaza si el correo pertenece a otra cuenta.
3. Un correo válido se guarda y persiste después de cerrar y volver a abrir la aplicación.
4. El cambio no modifica el teléfono, la identificación, el saldo ni el historial.
5. No se envían códigos de confirmación por correo.
6. Si el usuario cancela la edición o el cambio es rechazado, se conserva el correo anterior.

Definición transversal de terminado
Las siguientes condiciones se aplican a todas las historias cuando la función correspondiente las involucra. Complementan los criterios particulares y deben verificarse antes de cerrar una historia.
La aplicación es exclusivamente web y se adapta a pantallas de escritorio y móviles.
La autenticación, autorización, titularidad y validación de montos se comprueban en el servidor.
Los montos se almacenan con una representación decimal exacta y no mediante números de punto flotante.
Los usuarios, perfiles, billeteras, saldos y transacciones se conservan después de reiniciar la aplicación.
El sistema soporta al menos 20 usuarios concurrentes sin producir inconsistencias en los saldos.
Las contraseñas y secretos no aparecen en mensajes de error ni registros técnicos.
Los teléfonos y demás datos personales se ocultan parcialmente cuando no es necesario mostrarlos completos.
La navegación básica se puede realizar con teclado y los controles tienen etiquetas comprensibles.
Los formularios identifican los campos obligatorios y explican cómo corregir los errores.
Las funciones principales son accesibles mediante una navegación de no más de tres clics.
Los usuarios, el dinero y los demás datos empleados en pruebas son ficticios.
Los resultados de las operaciones se limitan a los estados exitosa y rechazada.
La recuperación o el restablecimiento de contraseña no forman parte del alcance.
Reglas de negocio consolidadas
Teléfono, número de identificación y correo electrónico son únicos por cuenta.
El teléfono funciona como identificador de inicio de sesión y destinatario de transferencias.
El teléfono y el correo pueden modificarse; el número de identificación permanece inmutable.
Al cambiar el teléfono, el anterior queda disponible para otro registro.
Las transferencias admiten valores entre $100 y $3.000.000 COP, inclusive.
Las recargas admiten valores entre $5.000 y $5.000.000 COP, inclusive.
La billetera no tiene un saldo máximo.
El historial presenta 20 movimientos por página y permite filtrar por fecha y tipo.
Una sesión expira después de cinco minutos sin actividad.
