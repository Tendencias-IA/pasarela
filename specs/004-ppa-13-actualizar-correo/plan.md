# Implementation Plan: PPA-13

Extender `accounts` y el perfil de PPA-12. Sin dependencias, migraciones ni cambios en auth.

## Design

- `PATCH /api/v1/profile` acepta `{email}` o `{phone}`, exactamente uno por solicitud.
- `UpdateEmailIn` reutiliza normalización y validación de HU-01; rechaza campos extra.
- Servicio transaccional bloquea el usuario, comprueba correo único excluyendo al titular
  y cambia solamente email; índice UNIQUE protege carreras. Errores RFC 9457 existentes.
- Respuesta: mismo perfil propio; 200 éxito, 401 sesión, 404 ausente, 409 duplicado, 422 formato.
- `EmailEditor` Ionic con React Hook Form; `useProfile.changeEmail` actualiza la caché.
- Cancelar no envía PATCH; rechazar conserva el correo y permite corregir la edición.

## Constitution Check

| Principio | Resultado | Evidencia |
| --- | --- | --- |
| Spec y trazabilidad | PASS | CA-1 a CA-6 |
| Modularidad | PASS | Solo accounts escribe users |
| Seguridad | PASS | Usuario desde sesión; validación estricta; sin PII en logs |
| Integridad del dinero | PASS | No modifica wallets ni transactions |
| Simplicidad | PASS | Reutiliza validadores, perfil e infraestructura |
| Calidad | PASS | Unitarias, MySQL, contrato y Playwright |

## Verification

Formato, normalización, campos extra, duplicados y cancelación. MySQL verifica persistencia
y que el perfil/saldo permanezcan intactos. Navegador: éxito, rechazo y cancelación en móvil
y escritorio. El diff del PR se compara contra PPA-12; se retargetea a main tras su merge.
