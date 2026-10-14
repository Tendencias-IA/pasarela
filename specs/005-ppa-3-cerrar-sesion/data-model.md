# Modelo existente

`sessions`: id, user_id, token_hash único, created_at, last_activity_at,
expires_at obligatorio, revoked_at nullable. Activa: revoked_at NULL y
expires_at futuro. Logout cambia solo revoked_at de NULL a hora UTC actual.
No altera users, wallets, transactions ni otras sesiones. Sin migración.
