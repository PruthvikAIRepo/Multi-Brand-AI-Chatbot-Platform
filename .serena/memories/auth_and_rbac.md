# Auth & RBAC (SRS §21)

See `mem:architecture_backend` for the dependency chain.

## Roles (Phase 1 — SRS §21.1)
- **Super Admin** — full system. Creates/edits/deletes brands; invites/assigns/revokes
  admins; manages secrets & system settings; views logs/analytics across ALL brands.
  Bypasses every permission check (`permissions.py`).
- **Admin** — scoped to assigned brand(s). Edits that brand's products/FAQs/routines/tone/
  image-style/compliance; views logs for assigned brands only. Cannot create/delete brands.
  Cannot manage users.
- **End user** — the chatbot visitor. No login; public brand-scoped endpoints.

## Permissions model (IMPORTANT nuance)
- DB has a 32-string per-brand permission set (`UserBrandAssignment.permissions` JSONB),
  enforced by `check_brand_permission(db, user, brand_id, "<perm>")`. Full list +
  `GET /api/v1/users/permissions/all`.
- **Phase 1 behavior (per owner + SRS §21.4): assign brand → Admin gets ALL permissions by
  default.** Narrowing to a subset = the "future revoke" path via
  `PUT /users/{id}/brands/{brand_id}/permissions`. **Granular per-feature roles are SRS
  Phase 2** — keep the capability, default-all for now. Invite has no per-permission picker yet.

## User management actions (SRS §21.4) — all Super-Admin-only except self password
- Invite admin (`POST /users`) — also assigns brand(s) at invite time (≥1 brand required).
- Assign/replace brands (`PUT /users/{id}/brands`).
- Deactivate/activate (`POST /users/{id}/deactivate|activate`) = revoke access.
- Unlock a brute-force lockout: `POST /users/{id}/unlock` (Super Admin).
- View any user's activity logs: `GET /logs/admin-activity?user_id=...` (Super Admin).
- Reset own password: any authenticated user (`/auth/change-password`).
- All mutating user-mgmt actions are audited with actor, **IP**, and before/after state
  (Unit 2). Frontend contract: `docs/AUTH_API.md`.

## Login flow (current, post Unit-1)
1. `POST /auth/login` — per-IP auth rate limit (fails open if Redis down), bcrypt verify.
2. Brute-force lockout: 5 fails → 15-min lock; the failed-attempt state is **committed**
   before raising (else get_db rollback would discard it — that was bug #3).
3. Unknown email runs a dummy bcrypt verify to equalize timing (anti-enumeration, #9).
4. Issues JWT access (30m) + refresh (7d, stored as sha256 hash).
5. **must_change_password gate**: a freshly seeded/invited user can only hit `/auth/me`,
   `/auth/change-password`, `/auth/logout` until they change the password (enforced in
   `get_current_user`). First Super Admin is seeded with this flag set.
6. LOGIN / FAILED_LOGIN are written to the audit trail with client IP.

## Email normalization
Emails are lowercased on **both** invite/seed (storage) and login (lookup) — keep them in
sync or mixed-case admins can't log in.

## Known gaps (see `mem:security_status`)
Distinct "Account locked"/"deactivated" messages still reveal account existence (UX vs
enumeration tradeoff). No refresh-token rotation yet. (User-management audit IP/before-after
was completed in Unit 2.)
