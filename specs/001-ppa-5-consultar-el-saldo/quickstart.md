# Quickstart: Consultar el saldo

## Prerequisites

- La rama contiene las dependencias de HU-02 y el entorno usa Python 3.12 y Node 22.
- MySQL local está disponible con las variables de `api/.env` o se usa el entorno de
  pruebas que crea MySQL mediante Testcontainers.
- Las migraciones, incluida `0002_wallet_tables` de HU-08, están aplicadas antes de probar
  la API de forma manual.

## Verification workflow

1. Crear datos ficticios: una cuenta, una sesión válida y una billetera con saldo
   persistido conocido.
2. Autenticarse como esa cuenta y consultar `GET /api/v1/wallet`; comprobar `200` y el
   saldo como cadena decimal exacta.
3. Consultar sin cookie o con sesión vencida; comprobar que no se devuelve ningún saldo.
4. Usar una cuenta de prueba sin billetera; comprobar `404 wallet_not_found`, sin crear
   una billetera ni devolver cero.
5. Aplicar una recarga exitosa mediante `POST /api/v1/wallet/recharges`; comprobar que la
   siguiente consulta devuelve el valor persistido actualizado. La comprobación análoga
   con transferencia se añadirá cuando HU-07 exista.
6. Ejecutar las pruebas de calidad desde `api/` y `webapp/` según `AGENTS.md`, incluidos
   los escenarios de HU-05 para escritorio y móvil.
7. Ejecutar la prueba nocturna de carga o su escenario de saldo para comprobar el p95 de
   dos segundos con 20 usuarios concurrentes.

## Manual browser flow

1. Iniciar sesión con una cuenta ficticia que tenga billetera.
2. Verificar que la pantalla principal muestra el saldo disponible en COP.
3. Confirmar que los estados de carga y error tienen texto accesible y que no se muestra
   saldo de una cuenta distinta.

