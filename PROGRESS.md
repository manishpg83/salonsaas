# PROGRESS — Salon SaaS (SalonOS)

Build tracker. **Claude Code: read this file first every session** to see where
we are, then continue from the first unchecked module. Tick a box and add a
one-line note only when a module meets the Definition of Done (CLAUDE.md §8).
The human commits after each module.

Status key:  `[ ]` not started · `[~]` in progress · `[x]` done & committed

---

## MVP

### Phase 0 — Foundation & setup
- [x] **0.1** Project bootstrap (settings split, .env, Postgres, DRF+JWT, health endpoint) — _note: `/api/v1/health/` live, 1 test passing; set real DB_PASSWORD in .env before running migrate_
- [x] **0.2** Core app: base models, tenancy, `SalonScopedViewSet`, permission skeleton — _note: no concrete models yet (FK to salons.Salon resolves lazily), 13 unit tests passing_

### Phase 1 — Auth & onboarding
- [x] **1.1** Custom user + JWT auth (register/login/refresh/logout/me) — _note: email-based User, token blacklist on logout; 11 tests passing (verified against sqlite locally — real DB_PASSWORD still needed in .env to migrate)_
- [ ] **1.2** OTP login + forgot/reset password (console sender) — _note:_
- [ ] **1.3** Salon, Branch & Membership + active-salon resolution — _note:_
- [ ] **1.4** Onboarding wizard (10 steps) + booking slug — _note:_

### Phase 2 — Services & catalog
- [ ] **2.1** Service categories & services (CRUD, tenant-scoped) — _note:_
- [ ] **2.2** Packages (MVP-light) — _note:_

### Phase 3 — Staff
- [ ] **3.1** Staff profiles + staff-service mapping — _note:_
- [ ] **3.2** Staff availability endpoint — _note:_

### Phase 4 — Customers (CRM)
- [ ] **4.1** Customer profile + history scaffold + search — _note:_

### Phase 5 — Appointments (core)
- [ ] **5.1** Appointment + AppointmentService + status flow — _note:_
- [ ] **5.2** Calendar views, filters & double-booking prevention — _note:_

### Phase 6 — Billing / POS
- [ ] **6.1** Invoice + items + payment (from completed appointment) — _note:_
- [ ] **6.2** Expenses — _note:_

### Phase 7 — Basic inventory
- [ ] **7.1** Products, suppliers, purchases, stock ledger, low-stock — _note:_
- [ ] **7.2** Service → stock consumption on completion — _note:_

### Phase 8 — WhatsApp transactional notifications
- [ ] **8.1** Messaging provider (console) + templates + Message log — _note:_
- [ ] **8.2** Transactional triggers (confirm / reminder / feedback / cancel) — _note:_

### Phase 9 — Dashboard
- [ ] **9.1** Dashboard aggregations (cards, schedule, revenue, insights) — _note:_

### Phase 10 — Reports
- [ ] **10.1** Sales / customer / appointment / inventory reports + CSV export — _note:_

> ✅ **MVP complete after Phase 10 — STOP and get real salon feedback.**

---

## Version 2 (do not start unprompted)
- [ ] Lead CRM & pipeline
- [ ] Customer auto-segmentation
- [ ] WhatsApp marketing campaigns & automations
- [ ] Membership plans
- [ ] Package usage tracking
- [ ] Staff attendance & commission
- [ ] Supplier / advanced inventory
- [ ] Reviews & feedback
- [ ] Public booking website + widget
- [ ] Granular per-action permissions

## Version 3
- [ ] AI business assistant
- [ ] AI campaign / copy generator
- [ ] Multi-branch rollup
- [ ] Advanced analytics
- [ ] Churn / profit prediction
- [ ] Automated reactivation
- [ ] White-label
- [ ] Super Admin panel & SaaS subscription billing (Razorpay)

---

## Decisions log
_Record any architecture decision or deviation here (date — decision — why)._

- 2026-—-— · Backend = Django + DRF + PostgreSQL (overrides blueprint's Node/Supabase recommendation).
- 2026-—-— · Multi-tenancy = shared DB, row-level `salon` scoping.
- 2026-08-18 · Consolidated CLAUDE.md/PROGRESS.md/requirements.txt/docs into `salonos/` (the actual git repo root, already linked to GitHub) — they had been created one level up by mistake.
- 2026-08-18 · `apps/core/permissions.py` defines a placeholder `Role` (plain strings) since `apps.salons.Membership` doesn't exist until Phase 1.3. Replace references with the real `Membership.role` TextChoices once that lands; `get_active_membership()` uses `apps.get_model("salons", "Membership")` for the same reason.
- 2026-08-18 · Enabled `rest_framework_simplejwt.token_blacklist` (bundled with the already-approved simplejwt package, not a new dependency) so `/auth/logout/` can actually invalidate a refresh token. Reminder for future auth-adjacent views: the project's `DEFAULT_PERMISSION_CLASSES` is `IsAuthenticated`, so any endpoint that must work *before* login (login itself, token refresh, register) needs an explicit `permission_classes = [AllowAny]` override — see `apps/accounts/views.py`.

## Blockers / open questions
_List anything waiting on the human._