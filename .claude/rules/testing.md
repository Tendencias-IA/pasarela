# Pruebas

Aplica a todo el repositorio. Principio III de la constitución: las pruebas se escriben
antes de la implementación y fallan primero. La API ≥ 90 % de cobertura de líneas y
ramas; la webapp con Vitest y un escenario Playwright por historia.

## Pirámide y dónde vive cada prueba

| Nivel | Qué prueba | Dónde | Necesita |
| --- | --- | --- | --- |
| Unitaria de la API | reglas de negocio en `service.py` con repositorios falsos | `api/app/modules/<m>/tests/unit/` | nada |
| Integración de la API | repositorio + servicio contra MySQL real: bloqueos, unicidad, migraciones | `api/app/modules/<m>/tests/integration/` | MySQL en contenedor |
| Contrato | cada respuesta cumple `openapi.yaml` | `api/tests/contract/` | app de pruebas |
| API end-to-end | flujo completo por HTTP (registro → login → recarga → transferencia) | `api/tests/e2e_api/` | MySQL |
| Unitaria de la webapp | componentes, hooks, `money/`, `problem.ts` | `webapp/src/**/__tests__/` | jsdom |
| E2E navegador | un spec por HU, escritorio y móvil, con axe | `webapp/e2e/` | API + MySQL |
| Carga | p95 de RNF-02 con 20 usuarios | `api/tests/load/locustfile.py` | ambiente completo; job nocturno, no bloquea PR |

La mayor parte de la cobertura del 90 % sale del nivel unitario: los servicios reciben
un repositorio falso (`FakeWalletRepository` en `tests/fakes.py`) y se prueban todas las
ramas sin base de datos. Razón: son rápidas, deterministas y la IA puede ejecutarlas en
cada tarea.

## Reglas comunes

- Nombre del test: `test_<accion>_<condicion>_<resultado>`:
  `test_confirm_transfer_insufficient_balance_rejects_without_changing_balances`.
- El docstring o el nombre cita el criterio: `"""HU-07 CA-6"""`. Cada CA de la spec tiene
  al menos un test que lo nombra; `grep "CA-" -r` debe encontrarlos.
- Patrón Arrange / Act / Assert con líneas en blanco entre bloques. Un comportamiento por
  test; varias aserciones sobre el mismo resultado están bien.
- Datos siempre ficticios y generados por factories (`tests/factories.py`,
  `e2e/fixtures/`), nunca teléfonos, cédulas ni nombres reales (RNF-06.3).
- Sin `sleep` para esperar; se usan esperas explícitas (Playwright `expect(...)`) o
  sincronización (eventos, `threading.Barrier`).
- Sin `@skip` ni `.only` en `main`. Un test que no se puede arreglar en el PR se borra
  con justificación en el cuerpo del PR, no se silencia.
- Montos en aserciones como `Decimal("150000.00")`, nunca `150000.0`.

## API

Configuración en `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = "--cov=app --cov-branch --cov-report=term-missing --cov-report=xml --cov-fail-under=90 -q"
testpaths = ["app", "tests"]

[tool.coverage.run]
omit = ["app/__main__.py", "migrations/*", "*/tests/*"]
```

- `conftest.py` raíz expone `app` (config `testing`), `client` (Flask test client),
  `db_session` con rollback por test y `logged_in_client(user)`.
- MySQL de pruebas con `testcontainers[mysql]` en local y como `services:` en CI. Las
  migraciones Alembic se aplican al iniciar la sesión de pruebas; nunca `create_all()`.
- Pruebas obligatorias de concurrencia para HU-07 y HU-08 en integración: dos hilos con
  `threading.Barrier` intentan gastar el mismo saldo; exactamente una pasa y el saldo
  final nunca es negativo (RNF-04.2). Y de idempotencia: misma clave dos veces produce
  un solo movimiento; misma clave con otro cuerpo responde `422` (ADR-0005).
- Pruebas de contrato con `schemathesis` apuntando a `openapi.yaml` contra la app de
  pruebas; cualquier respuesta fuera de contrato falla.

```python
def test_confirm_transfer_concurrent_requests_never_overdraw(db_session, two_users):
    """HU-07 CA-9, RNF-04.2"""
    sender, receiver = two_users
    wallet_service.recharge(sender.id, Decimal("100000.00"))   # la clave la gestiona @idempotent en la ruta
    barrier = threading.Barrier(2)
    results: list[Exception | None] = []

    def attempt() -> None:
        barrier.wait()
        try:
            transfer_service.confirm_transfer(sender.id, receiver.phone, Decimal("100000.00"))
            results.append(None)
        except InsufficientBalance as exc:
            results.append(exc)

    threads = [threading.Thread(target=attempt) for _ in range(2)]
    for t in threads: t.start()
    for t in threads: t.join()

    assert sum(r is None for r in results) == 1
    assert wallet_repository.get_balance(sender.id) == Decimal("0.00")
```

## Webapp

- Vitest con Testing Library: se prueba comportamiento observable (lo que ve el usuario),
  no implementación. Consultas por rol y etiqueta, igual que Playwright.
- `shared/money` y `shared/api/problem.ts` al 100 %: son la lógica que decide qué se
  muestra ante montos y errores.
- Mock de red con MSW (`src/test/server.ts`) usando respuestas que cumplen
  `openapi.yaml`; nunca se mockea `fetch` a mano.
- Playwright: configuración en `webapp/playwright.config.ts` con `baseURL` de la app
  servida por Vite en modo preview contra una API real con MySQL (CI levanta ambos).
  `retries: 0` en local, `1` en CI; traza y vídeo solo en fallo.

## Definición de "probado" para cerrar una tarea

1. Los tests nuevos fallaron antes del cambio y pasan después (se indica en el PR).
2. Cobertura de la API ≥ 90 % en el reporte de `pytest-cov`, sin excluir archivos
   nuevos.
3. Cada CA de la HU tiene un test que lo cita, en el nivel adecuado.
4. El spec de Playwright de la HU pasa en `desktop-chromium` y `mobile-chromium` sin
   violaciones `serious`/`critical` de axe.
