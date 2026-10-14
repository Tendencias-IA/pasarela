# Quickstart: Validate HU-01 Account Registration

This guide describes the runnable checks expected after `$speckit-implement`. It does
not implement the feature.

## Prerequisites

- Python 3.12 and Node.js 22, or Docker with Compose.
- MySQL 8 reachable through the repository's `docker-compose.yml`.
- A local `.env` copied from `.env.example` with fictitious development credentials.

## 1. Prepare the database

```powershell
Copy-Item .env.example .env
docker compose up -d mysql
Set-Location api
flask db upgrade
```

Expected: the login base migration creates `users` and `sessions`; the HU-01 migration
extends `users` and creates `wallets`, including all unique, foreign-key and
balance constraints described in [data-model.md](data-model.md).

## 2. Run API quality gates

```powershell
Set-Location api
ruff format --check .
ruff check .
mypy app
pytest
```

Expected:

- All tests pass and line/branch coverage is at least 90%.
- Unit tests cite HU-01 acceptance criteria and cover every validation branch.
- MySQL integration tests prove identification-number uniqueness, concurrent duplicate rejection and
  rollback when wallet creation fails.
- Contract tests validate responses against `api/openapi.yaml`, whose HU-01 slice must
  match [contracts/accounts.openapi.yaml](contracts/accounts.openapi.yaml).
- A persistence assertion confirms the stored credential is an Argon2id hash and never
  the submitted password.

## 3. Run webapp quality gates

```powershell
Set-Location webapp
npm run lint
npm run typecheck
npm run test -- --coverage
npm run build
```

Expected: the registration form exposes all required accessible labels, links every
error to its field, prevents a duplicate in-flight submission and renders RFC 9457 field
errors returned by MSW.

## 4. Run the complete stack and browser scenarios

```powershell
Set-Location ..
docker compose --profile app up --build -d
Set-Location webapp
npm run e2e
```

Expected: `hu-01-registrar-cuenta.spec.ts` passes on `desktop-chromium` and
`mobile-chromium`, with no serious or critical axe violations.

## 5. Manual contract smoke test

Use only fictitious values:

```powershell
$body = @{
  full_name = "Ana Prueba"
  phone = "3000000000"
  national_id = "TEST12345"
  email = "ana@example.test"
  password = "segura123"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8080/api/v1/accounts" `
  -Headers @{ "X-Requested-With" = "fetch" } `
  -ContentType "application/json" `
  -Body $body
```

Expected response: HTTP `201`, a generated `account_id`, and
`wallet.balance == "0.00"`. No authentication cookie is created.

Repeat the same request. Expected response: HTTP `409` with
`Content-Type: application/problem+json`, `code == "duplicate_identity"`, and no second
account or wallet.

Submit multiple invalid fields. Expected response: HTTP `422` with one `errors[]` item
per invalid field and no persisted rows.

## 6. Privacy and atomicity checks

- Search application logs and responses for the submitted plaintext password and
  identification number; neither may appear.
- Force the wallet repository to fail in its integration test and verify that both
  `users` and `wallets` counts remain unchanged.
- Send two concurrent requests with the same identity and verify that exactly one
  returns `201`, the other returns `409`, and only one user-wallet pair exists.
