---
paths:
  - "api/**"
---

# API (`api/`): Python 3.12 + Flask 3 + SQLAlchemy 2 + MySQL 8

Aplica a todo archivo bajo `api/`. La estructura de módulos está en `architecture.md`;
aquí van las convenciones de código. Decisiones de stack en `docs/adr/0002`.

## Herramientas obligatorias

| Herramienta | Configuración | Falla el CI si |
| --- | --- | --- |
| Ruff (lint + format) | `[tool.ruff]` en `pyproject.toml`, `line-length = 100`, reglas `E,F,I,B,UP,S,N,SIM` | cualquier hallazgo |
| mypy | `strict = true`, `plugins = ["pydantic.mypy"]` | cualquier error |
| pytest + pytest-cov | `--cov=app --cov-branch --cov-fail-under=90` | cobertura < 90 % o un test rojo |

Ejecutar antes de cada commit, en este orden:

```bash
cd api && ruff format . && ruff check . && mypy app && pytest
```

## App factory y configuración

- `create_app(config_name: str | None = None) -> Flask` en `app/__init__.py` registra
  extensiones, blueprints y manejadores de error. Si `config_name` es `None`, lo toma de
  la variable de entorno `APP_CONFIG` (por defecto `development`). Así la CLI de Flask
  (`FLASK_APP=app flask db upgrade`) y gunicorn (`app:create_app()`) funcionan sin
  argumentos, y las pruebas pasan el nombre explícito. Nunca se crea `Flask(__name__)` a
  nivel de módulo. Razón: las pruebas necesitan construir una app por test con
  configuración distinta.
- La configuración se lee de variables de entorno en `app/config.py`
  (`DATABASE_URL`, `SECRET_KEY`, `SESSION_IDLE_MINUTES=5`, `LOG_LEVEL`). Sin valores por
  defecto para secretos: si falta `SECRET_KEY`, la app no arranca. Hay un
  `api/.env.example` con todas las claves y valores de ejemplo no sensibles.
- Cuatro configs en `app/config.py`: `development` (local, cookie sin `Secure`),
  `testing` (pytest: `TESTING=True`, rate limit desactivado), `e2e` (igual que
  `production` pero cookie sin `Secure` y rate limit desactivado, porque Playwright y
  Locust usan `http://127.0.0.1`) y `production` (`Secure`, `DEBUG=False`). `FLASK_ENV`
  no se usa: Flask 3 lo ignora.

## Rutas (Blueprints)

- Un Blueprint por módulo, prefijo `/api/v1/<recurso>`, registrado en `create_app`.
- La ruta hace exactamente cuatro cosas: autenticar (decorador), parsear y validar con el
  schema de entrada, llamar a una función del servicio, serializar con el schema de
  salida. Nada más.

```python
# Correcto
@bp.post("/recharges")
@login_required
@idempotent
def create_recharge() -> tuple[dict[str, Any], int]:
    payload = RechargeIn.model_validate(request.get_json())
    result = service.recharge(current_user().id, payload.amount)  # la clave la gestiona @idempotent
    return RechargeOut.from_domain(result).model_dump(), 201
```

```python
# Incorrecto
@bp.post("/recharges")
def create_recharge():
    data = request.get_json()
    if Decimal(data["amount"]) < 5000:            # regla de negocio en la ruta
        return {"error": "monto inválido"}, 400     # formato de error ad hoc
    wallet = Wallet.query.filter_by(user_id=session["uid"]).first()  # SQL en la ruta
    wallet.balance += Decimal(data["amount"])
    db.session.commit()
    return {"ok": True}
```

Diferencia: en la segunda versión la regla, la consulta y el formato de error viven en la
ruta, así que no se pueden probar sin Flask ni reutilizar, y el error no sigue RFC 9457.

## Schemas (Pydantic 2)

- `schemas.py` define `XxxIn` para entrada y `XxxOut` para salida. Los montos se tipan
  como `Decimal` con `condecimal(max_digits=15, decimal_places=2, gt=0)` y se serializan a
  cadena (`model_config = ConfigDict(json_encoders=...)` o `field_serializer`).
- La validación de formato (teléfono de 10 dígitos, correo, contraseña de 8+ con letra y
  número) vive en el schema con validadores de campo. La validación de negocio (unicidad,
  saldo, límites por tipo de operación) vive en el servicio. Razón: el schema no tiene
  acceso a la base de datos y no debe tenerlo.
- Los mensajes de validación se escriben en español y nombran el campo: la respuesta de
  error incluye `errors: [{"field": "phone", "message": "..."}]` (HU-01 CA-3).

## Servicios

- Funciones puras de módulo (no clases con estado) que reciben ids y valores de dominio y
  devuelven dataclasses `frozen=True` definidas en el mismo `service.py` o en
  `app/common/`. Nunca reciben `request` ni devuelven `Response`.
- El servicio abre la transacción con `with db.session.begin():` cuando escribe. Los
  servicios llamados desde otro servicio no abren ni cierran transacciones; reciben la
  sesión implícita.
- Errores de negocio son excepciones que heredan de `AppError` (`app/common/errors.py`)
  con `status`, `code` y `detail`, nombradas con sufijo `Error` (regla N818 de Ruff): `InsufficientBalanceError`, `RecipientNotFoundError`,
  `SelfTransferError`, `AmountOutOfRangeError`, `DuplicateIdentityError`, `InvalidCredentialsError`,
  `SessionExpiredError`. El manejador global las convierte a RFC 9457. Nunca `return None`
  para señalar fallo.
- Un servicio que no se puede nombrar sin "y" se divide (`validate_and_transfer` →
  `preview_transfer` + `confirm_transfer`).

## Repositorios y modelos

- Modelos con `Mapped[]` y `mapped_column`, tabla en `__tablename__`, `created_at` y
  `updated_at` con `server_default=func.now()`.
- Consultas con `select()` de SQLAlchemy 2; nunca `Model.query` legado. Los bloqueos se
  escriben explícitos: `select(Wallet).where(Wallet.id.in_(ids)).order_by(Wallet.id)
  .with_for_update()`.
- Sin `commit()` en repositorios. Sin `db.session` fuera de `repository.py` salvo el
  `begin()` del servicio.
- Toda modificación de esquema lleva una migración Alembic generada con `flask db
  migrate -m "ppa-n descripcion"` y revisada a mano (autogenerate olvida `CHECK` y
  tipos `DECIMAL`).

## Errores y logs

- Nunca `except Exception: pass`. Se captura la excepción concreta o se deja propagar al
  manejador global, que responde `500` con un `problem` genérico y registra el stack
  trace con `request_id`.
- Los mensajes de error al cliente no revelan si existe el teléfono, cuál credencial
  falló ni detalles internos (HU-02 CA-3, RNF-01.5).
- Logging estructurado con el logger de `app/common/logging.py`; nunca `print`. Nunca
  se registra `password`, `password_hash`, el id de sesión ni teléfonos completos; el
  helper `mask_phone` es obligatorio al loguear un teléfono (RNF-06.4).

## Convenciones de nombres

- Módulos y archivos en `snake_case`, clases en `PascalCase`, constantes en
  `UPPER_SNAKE`. Identificadores en inglés; mensajes al usuario y comentarios en español.
- Nombres de tabla en plural (`users`, `wallets`), columnas en `snake_case`, FK como
  `<tabla_singular>_id`.
- Funciones de servicio con verbo: `register_account`, `preview_transfer`,
  `confirm_transfer`, `recharge`, `list_movements`.

## Dependencias

Añadir una dependencia requiere ADR corto en `docs/adr/` y commit propio
(`build(PPA-n): add <paquete>`), nunca mezclado con la funcionalidad. Versiones fijadas
en `pyproject.toml` con `~=`. Lista inicial permitida: `flask`, `flask-sqlalchemy`,
`flask-migrate`, `sqlalchemy`, `alembic`, `pymysql`, `cryptography` (autenticación de
MySQL 8), `pydantic`, `argon2-cffi`, `flask-limiter`, `python-json-logger`, `gunicorn`;
dev: `pytest`, `pytest-cov`, `pytest-mock`, `ruff`, `mypy`, `testcontainers[mysql]`,
`schemathesis`; extra `load` (solo el job nocturno): `locust`, porque registra un plugin de
pytest que cuelga la recolección de pruebas.
