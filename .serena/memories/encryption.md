# At-rest encryption & secret handling

See `mem:core`. Module: `backend/app/core/encryption.py`. Used by `secret_service`
(brand API keys) and `lead_service` (lead email/phone PII). Both columns are `LargeBinary`.

## Scheme (after #7, Unit 3)
- **AES-256-GCM** authenticated encryption (tamper is detected). Satisfies SRS §3.10 "AES-256".
- Keys derived from config strings via **HKDF-SHA256** (replaced the old raw single-pass SHA-256).
- Blob format: `b"GCM1" || nonce(12) || ciphertext+tag`. Random nonce per encryption.
- Public API unchanged: `encrypt(str) -> bytes`, `decrypt(bytes) -> str`. Also
  `hash_value` (email dedup), `mask_email`, `mask_phone` (display).

## Key rotation
- `ENCRYPTION_KEY` = primary (encrypts all new data). `ENCRYPTION_KEYS_RETIRED` =
  comma-separated old keys, tried on decrypt only. `decrypt` tries every key (the
  MultiFernet pattern), so rotation never orphans data.
- Procedure: (1) set `ENCRYPTION_KEYS_RETIRED=<old key>` and `ENCRYPTION_KEY=<new key>`;
  (2) data re-encrypts under the new primary whenever a secret/lead is updated;
  (3) drop the old key from `ENCRYPTION_KEYS_RETIRED` once nothing uses it.
- There is no bulk re-encrypt command yet (decrypt-with-any-key keeps things correct;
  add a maintenance task if a hard cutover is ever needed).

## Backward compatibility
- Pre-#7 data used unauthenticated AES-256-CBC (`IV(16) || ciphertext`, key = SHA-256(key)).
  `decrypt` detects the absence of the `GCM1` magic and falls back to that legacy path, so
  existing blobs still decrypt. New writes always use GCM.

## Rules
- Secrets/PII are NEVER returned decrypted by any API (only `****<last4>` / masked). See
  `mem:auth_and_rbac` (secrets are Super-Admin-only).
- The fail-closed config guard (`mem:security_status`) refuses to boot in prod with a default
  `ENCRYPTION_KEY`, so a weak at-rest key can't ship.

## Tests
`backend/tests/test_encryption.py` — round-trip, GCM format, tamper detection, wrong-key
rejection, rotation, legacy-CBC fallback.
