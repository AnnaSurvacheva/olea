# AI Psychologist Backend

Backend API for a self-discovery and daily reflection application built with FastAPI.

Refresh tokens are opaque random values; only their SHA-256 hex digests are stored
in `refresh_tokens.token_hash`. Their lifetime is configured with
`REFRESH_TOKEN_TTL_DAYS` (default: 30 days).

Successful login returns an access token and a refresh token. Send the refresh
token to `POST /auth/refresh` to rotate the token pair. Reuse of a previously
rotated refresh token revokes its entire token family and emits a security event;
security logs never include refresh-token values.

`POST /auth/logout` revokes the presented token's complete family and is
idempotent. Scheduled cleanup can call the `PurgeExpiredTokens` use case; it
deletes expired rows immediately and keeps revoked rows for
`REVOKED_REFRESH_TOKEN_RETENTION_DAYS` (default: 30 days) before deletion.
