# Research: Registrar una cuenta

## Decision 1: First vertical and module boundary

**Decision**: Implement the use case in `accounts` and expose a narrow
`wallet.service.create_wallet_for_account(user_id)` operation. `accounts.service` owns
the transaction and invokes the wallet service after flushing the new user id.

**Rationale**: This follows ADR-0001 and lets each module own its table while satisfying
the atomic account-plus-wallet requirement.

**Alternatives considered**:

- Creating `wallets` from `accounts.repository`: rejected because a module may not touch
  another module's table.
- Moving registration to a cross-cutting orchestration module: rejected as an extra
  abstraction for a single use case.
- Committing the user before creating the wallet: rejected because it permits partial
  accounts.

## Decision 2: Transaction and concurrency boundary

**Decision**: Execute user insertion and wallet insertion in one
`db.session.begin()` block. Enforce uniqueness in MySQL and translate the relevant
`IntegrityError` into a generic `409 duplicate_identity` after rollback.

**Rationale**: Application-side existence checks improve feedback but cannot prevent a
race. Database unique constraints are the final authority and the transaction prevents
partial data.

**Alternatives considered**:

- Check-then-insert without constraints: rejected because concurrent requests can both
  pass the check.
- Locking the whole users table: rejected as unnecessary and harmful to concurrency.
- Returning raw database errors: rejected because they expose internals and can include
  personal data.

## Decision 3: Canonical identity values

**Decision**: Strip surrounding whitespace; store email in lowercase and the
`national_id` in uppercase. Store the Colombian mobile phone as the validated
10-character string. Enforce unique indexes on phone, email and identification number.

**Rationale**: The specification says comparisons ignore case where letters are
accepted. Canonical storage makes the rule explicit instead of depending on a database
collation.

**Alternatives considered**:

- Preserve multiple display and comparison columns: rejected because no requirement
  asks to preserve input casing.
- Depend only on a case-insensitive MySQL collation: rejected because the business rule
  would be implicit and environment-dependent.
- Add an identification-type field: rejected because HU-01 and the central requirement
  require only the identification number.

## Decision 4: Password protection

**Decision**: Hash passwords in `accounts.service` with `argon2-cffi`'s Argon2id
`PasswordHasher` and persist only `password_hash`. Never return or log the password or
hash.

**Rationale**: Argon2id is mandated by the constitution and security rules and is in the
approved dependency set.

**Alternatives considered**:

- General-purpose hashes such as SHA-256: rejected because they are not password hashing
  algorithms.
- Encryption with a reversible key: rejected because the application never needs to
  recover a password.
- Hashing in the route or browser: rejected because the service owns the security rule
  and transport still requires HTTPS.

## Decision 5: HTTP result and error semantics

**Decision**: `POST /api/v1/accounts` requires JSON and
`X-Requested-With: fetch`, returns `201` with the new account id and wallet balance
`"0.00"`, returns an RFC 9457 `422 validation` containing all field errors, and returns
a generic RFC 9457 `409 duplicate_identity` without naming the conflicting value.

**Rationale**: This conforms to the repository API conventions, gives the client enough
information to confirm creation and avoids leaking another account's data.

**Alternatives considered**:

- Return `204`: rejected because the UI must confirm that the associated wallet exists
  with the expected initial balance.
- Return every submitted account field: rejected as unnecessary PII exposure.
- Identify the exact duplicate value in the response: rejected because it enables
  account enumeration.

## Decision 6: Validation ownership

**Decision**: Pydantic validates required fields and formats; the service canonicalizes
values, evaluates uniqueness and hashes the password; MySQL constraints guarantee final
integrity. The React form mirrors format rules only for immediate feedback and always
renders server `errors[]` as authoritative.

**Rationale**: Each rule is enforced at the lowest layer that can guarantee it without
putting database access in schemas or business authority in the browser.

**Alternatives considered**:

- Browser-only validation: rejected by RNF-01.4.
- Database-only validation: rejected because it cannot provide complete, accessible
  field feedback.
- Database calls from Pydantic validators: rejected because schemas must remain free of
  persistence concerns.

## Decision 7: Registration UI

**Decision**: Add a public `/registro` route with one accessible form, a field for each
required value, inline errors linked with `aria-describedby`, and a non-color-only
success or rejection message. Disable the submit button while the request is in flight.

**Rationale**: This satisfies the confirmed web scope and RNF-03 while remaining a
single-page vertical.

**Alternatives considered**:

- Multi-step registration: rejected because the number of fields does not justify the
  extra state and the requirements ask for one registration action.
- Global state management: rejected because the form is local and the project forbids
  speculative dependencies.
- Automatically log in after registration: rejected as explicitly out of scope.

## Decision 8: Test strategy for the initial scaffold

**Decision**: Write service and schema tests first, integration tests against MySQL for
constraints, concurrency and rollback, contract tests against OpenAPI, component tests
with MSW, and one Playwright HU-01 spec covering successful and rejected registration in
desktop and mobile projects with axe checks.

**Rationale**: This covers every acceptance criterion at the cheapest reliable level and
meets the constitution's ≥90% API coverage and per-HU browser requirement.

**Alternatives considered**:

- SQLite integration tests: rejected because MySQL constraint and transaction behavior
  is part of the feature.
- E2E-only coverage: rejected as slow and insufficient for all validation branches.
- Mocking `fetch` directly: rejected because repository rules require MSW and contract-
  shaped responses.

## Decision 9: Identification aligned with the requirement source

**Decision**: Model one globally unique `national_id` field and no
identification-type field.

**Rationale**: This directly matches requirements v1.0 and Jira PPA-1, avoiding a second
business concept that the source does not request.

**Alternatives considered**:

- Add type plus number: rejected because it introduces a field absent from the source.
- Store several identification values per account: rejected because the requirement
  defines one immutable number.
- Treat the choice as an ADR: rejected because it is a business rule, not architecture.
