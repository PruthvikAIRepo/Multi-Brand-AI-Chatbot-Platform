# Auth & User Management API — Frontend Guide

Reference for the **Super Admin / Admin** login and user-management surface. All paths are
prefixed with `/api/v1`. Phase-1 roles only (Super Admin, Admin).

## Response envelope

Every response uses a consistent shape.

**Success** (`200`):
```json
{ "data": { ... }, "message": "Success", "meta": { ... } }   // meta only on lists
```
**Error** (`4xx`/`5xx`):
```json
{ "data": null, "message": "Human-readable reason", "errors": ["detail", "..."] }
```
Validation errors (`422`) put field errors in `errors`, e.g. `"body -> email: value is not a valid email address"`.

## Auth header
All protected endpoints require:
```
Authorization: Bearer <access_token>
```
Access token lifetime ~30 min. Use the refresh token to get a new one.

---

## Authentication — `/api/v1/auth`

| Method | Path | Auth | Body | Notes |
|---|---|---|---|---|
| POST | `/auth/login` | public | `{ email, password }` | Rate-limited per IP. |
| POST | `/auth/refresh` | public | `{ refresh_token }` | **Rotates**: returns a new access token **and a new refresh token**; the presented refresh token is revoked. Store the new one and discard the old. Presenting a revoked token logs out all sessions (reuse detection). |
| POST | `/auth/change-password` | Bearer | `{ current_password, new_password }` | Allowed even while `must_change_password`. |
| POST | `/auth/forgot-password` | public | `{ email }` | Always 200 (no enumeration). Rate-limited. |
| POST | `/auth/reset-password` | public | `{ token, new_password }` | Token from email; single-use, 1-hour expiry. |
| POST | `/auth/logout` | public | `{ refresh_token }` | Revokes that refresh token. |
| GET | `/auth/me` | Bearer | — | Current user + assigned brands. Works while gated. |
| PUT | `/auth/me` | Bearer | `{ full_name }` | Blocked while `must_change_password`. |

**Login success `data`:**
```json
{ "access_token": "...", "refresh_token": "...", "token_type": "bearer", "must_change_password": true }
```

**`GET /auth/me` `data`:**
```json
{
  "id": "uuid", "email": "...", "full_name": "...", "role": "super_admin|admin",
  "is_active": true, "must_change_password": false,
  "assigned_brands": [ { "brand_id": "uuid", "permissions": ["products.view", ...] } ]
}
```

### Password policy (`new_password`)
≥8 chars, ≥1 uppercase, ≥1 lowercase, ≥1 digit, ≥1 special (`!@#$%^&*(),.?":{}|<>`). Violations → `422`.

### First-login flow (IMPORTANT for the UI)
A newly seeded Super Admin or invited Admin has `must_change_password: true`.
- While true, **every endpoint except** `GET /auth/me`, `POST /auth/change-password`,
  `POST /auth/logout` returns **`403`** with message *"Password change required..."*.
- The frontend should: on login (or when `/auth/me` shows the flag), force the
  change-password screen, then proceed normally.

### Lockout & rate limits
- **Account lockout:** 5 failed logins → locked 15 min. Login returns `401`
  *"Account locked. Try again in N minutes."* A Super Admin can clear it via the unlock endpoint.
- **Per-IP auth limit:** ~10 attempts / 5 min across login/forgot/reset → `429`.

---

## User Management — `/api/v1/users` (Super Admin only)

All return `403` for non-Super-Admin. Every mutating action is recorded in the audit log
(actor, timestamp, **IP**, action, before/after state).

| Method | Path | Body | Purpose |
|---|---|---|---|
| POST | `/users` | `{ email, full_name, role, brand_ids[] }` | Invite admin + assign brand(s). `role` defaults `admin`; ≥1 brand required; cannot invite a Super Admin. |
| GET | `/users` | — (`?page=&per_page=`) | List users (paginated). |
| GET | `/users/permissions/all` | — | The full list of assignable permission strings (for checkbox UI). |
| GET | `/users/{user_id}` | — | One user + assigned brands & permissions. |
| PUT | `/users/{user_id}/brands` | `{ brand_ids[] }` | Replace brand assignments (grants all permissions on each by default). |
| PUT | `/users/{user_id}/brands/{brand_id}/permissions` | `{ permissions[] }` | Narrow/restore the permission subset for one brand. |
| POST | `/users/{user_id}/deactivate` | — | Revoke access; revokes all tokens. Cannot deactivate self. |
| POST | `/users/{user_id}/activate` | — | Reactivate (also clears lockout). |
| POST | `/users/{user_id}/unlock` | — | Clear a brute-force lockout without changing active state. |
| POST | `/users/{user_id}/reset-password` | — | Email a single-use reset link to the user (help a locked-out admin / resend onboarding). Never sets or reveals a password. Returns 200 even if the account is inactive/absent. |

**Invite response `data`**: in **production** the `temp_password` is delivered **only by email** and is NOT in the response. In **development** it is returned in `data.temp_password` so you can test without SMTP.

### Permission model (Phase 1)
Assigning a brand grants the Admin **all** permissions on it by default. Use the
`.../permissions` endpoint to restrict to a subset later (the "revoke" path). Granular
per-feature roles are a Phase-2 expansion.

---

## Audit log — `/api/v1/logs/admin-activity` (Super Admin only)

`GET /logs/admin-activity?user_id=&brand_id=&action_type=&page=&per_page=`

Returns paginated admin actions: `user_id`, `action_type` (`login`, `failed_login`,
`invited`, `updated`, `disabled`, `enabled`, ...), `entity_type`, `entity_id`, `ip_address`,
`before_state`, `after_state`, `created_at`. This is how a Super Admin reviews what any
admin (or themselves) did. Brand-scoped logs (compliance/moderation/rag) live under
`/brands/{brand_id}/logs/...`.

---

## Common status codes
`400` bad request · `401` unauthenticated / bad login / locked · `403` forbidden (wrong role,
missing brand permission, or password-change-required) · `404` not found · `409` already exists
(e.g. duplicate email) · `422` validation · `429` rate limited.

> Note: emails are case-insensitive (normalized to lowercase) on both invite and login.
