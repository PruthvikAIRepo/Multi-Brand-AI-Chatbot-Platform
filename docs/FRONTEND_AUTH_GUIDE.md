# Frontend Developer Guide — Authentication (Postman)

Everything you need to integrate the **login / authentication** for the Multi-Brand AI
Chatbot admin panel. This covers making the calls in Postman, the token model, and the
**one-time password-change flow** you must handle in the UI.

> Scope: this guide covers **only the authentication endpoints**, which are tested and live.
> Other admin endpoints (users, brands, products, etc.) are still being finalized and will be
> documented once verified — please don't build against them yet.

---

## 1. Environment

| | |
|---|---|
| **Live API base URL** | `https://chatbot-api-721332751968.us-central1.run.app/api/v1` |
| **Interactive API docs (Swagger)** | `https://chatbot-api-721332751968.us-central1.run.app/docs` |
| **OpenAPI spec (import into Postman)** | `https://chatbot-api-721332751968.us-central1.run.app/openapi.json` |
| **Health check** | `GET /health` → `{"status":"...","checks":{"api":"ok","database":"ok",...}}` |

> **Tip:** In Postman, click **Import → Link** and paste the **openapi.json** URL above — it
> auto-generates the request collection for you. Then just set the variables below.

### Your test login
A test account has been created for you. **Get the email + temporary password from Pruthvik**
(not stored in this doc for security). On first login you'll be required to change the
password — see Section 4.

---

## 2. Postman setup (do this once)

Create a Postman **Environment** with these variables:

| Variable | Initial value |
|---|---|
| `base_url` | `https://chatbot-api-721332751968.us-central1.run.app/api/v1` |
| `access_token` | *(leave empty — filled automatically)* |
| `refresh_token` | *(leave empty — filled automatically)* |

**Auto-capture the tokens:** open the **Login** request → **Scripts / Tests** tab → paste:
```javascript
const d = pm.response.json().data;
if (d) {
  if (d.access_token)  pm.environment.set("access_token",  d.access_token);
  if (d.refresh_token) pm.environment.set("refresh_token", d.refresh_token);
}
```
Now every login/refresh auto-saves the tokens, and protected requests can use
`{{access_token}}` without copy-pasting.

**For protected requests:** in the request's **Authorization** tab choose
**Type = Bearer Token** and set the token to `{{access_token}}`.

---

## 3. Response format (every endpoint)

**Success:**
```json
{ "data": { ... }, "message": "Success" }
```
**Error:**
```json
{ "data": null, "message": "Reason", "errors": ["detail", "..."] }
```

---

## 4. THE LOGIN FLOW (important for the UI)

### Step 1 — Login
`POST {{base_url}}/auth/login`
Body (raw JSON):
```json
{ "email": "YOUR_EMAIL", "password": "YOUR_PASSWORD" }
```
Success `200`:
```json
{
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "....",
    "token_type": "bearer",
    "must_change_password": true
  },
  "message": "Login successful"
}
```

### Step 2 — Handle `must_change_password`  ⚠️ REQUIRED
If `must_change_password` is **true** (always true on a brand-new account):
- The user can ONLY call: `GET /auth/me`, `POST /auth/change-password`, `POST /auth/logout`.
- **Every other endpoint returns `403`** with message *"Password change required..."*.
- **The UI must detect this flag and route the user to a "Set new password" screen** before
  allowing anything else.

Change the password:
`POST {{base_url}}/auth/change-password` (Bearer token required)
```json
{ "current_password": "TEMP_PASSWORD", "new_password": "NewStrong#2026" }
```
Password rules: **min 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special** (`!@#$%^&*(),.?...`).
Success `200`: `"Password changed successfully"`. The gate is now cleared for this user.

### Step 3 — Read the current user
`GET {{base_url}}/auth/me` (Bearer)
```json
{
  "data": {
    "id": "uuid", "email": "...", "full_name": "...",
    "role": "super_admin",           // or "admin"
    "is_active": true,
    "must_change_password": false,
    "assigned_brands": [ { "brand_id": "uuid", "permissions": ["..."] } ]
  }
}
```
Use `role` for menu rendering, and `assigned_brands` to know which brands an Admin can see.

### Step 4 — Update own profile (optional)
`PUT {{base_url}}/auth/me` (Bearer)
```json
{ "full_name": "New Name" }
```

### Step 5 — Keep the session alive (token refresh)
Access tokens expire in **30 minutes**. Before/after expiry, call:
`POST {{base_url}}/auth/refresh`
```json
{ "refresh_token": "{{refresh_token}}" }
```
Returns a **new** `access_token` **and** a **new** `refresh_token` — store both, discard the old.
> The old refresh token is now dead. If a *revoked/rotated* token is ever replayed, the API
> returns `401 "reuse detected"` and logs the user out of all sessions (theft protection).
> A normal logged-out/expired token just returns `401 "Invalid or expired refresh token"`.

### Step 6 — Logout
`POST {{base_url}}/auth/logout`
```json
{ "refresh_token": "{{refresh_token}}" }
```
Revokes that refresh token. (Clear the stored tokens in the app.)

### Password reset (forgot password)
- `POST /auth/forgot-password` → `{ "email": "..." }` (always returns success; sends an email link)
- `POST /auth/reset-password` → `{ "token": "...", "new_password": "..." }`

---

## 5. Auth endpoints — quick reference (the only endpoints to build against for now)

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| POST | `/auth/login` | public | Log in → tokens + `must_change_password` |
| POST | `/auth/refresh` | public | Rotate tokens (new access + refresh) |
| POST | `/auth/change-password` | Bearer | Change own password (clears the first-login gate) |
| POST | `/auth/forgot-password` | public | Request a reset email |
| POST | `/auth/reset-password` | public | Reset password using the emailed token |
| POST | `/auth/logout` | public | Revoke the refresh token |
| GET | `/auth/me` | Bearer | Current user + role + assigned brands |
| PUT | `/auth/me` | Bearer | Update own full name |
| GET | `/health` | public | Service health check |

---

## 6. Status codes
`200` OK · `400` bad request · `401` not authenticated / bad login / locked · `403` forbidden
(**or password-change-required**) · `404` not found · `422` validation error ·
`429` too many attempts (rate limited).

## 7. Notes
- All timestamps are UTC ISO-8601.
- Brute-force: 5 wrong logins locks the account for 15 minutes.
- Emails are case-insensitive (stored lowercase).
- CORS is currently open for testing; it will be locked to the admin-panel domain before launch.

---

**Quickest start:** import the **openapi.json** into Postman, set the 3 environment variables,
add the token-capture script to the Login request, then walk Steps 1→6 above. The live
**Swagger** page is also fully interactive if you prefer clicking to test.
