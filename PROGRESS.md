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
- [x] **1.1** Custom user + JWT auth (register/login/refresh/logout/me) — _note: email-based User, token blacklist on logout; 24 tests passing against real Postgres_
- [x] **1.2** OTP login + forgot/reset password (console sender) — _note: `OTP` model (LOGIN/PASSWORD_RESET), pluggable `ConsoleOTPSender` (prints code), registered in admin for QA; 34 tests passing_
- [x] **1.3** Salon, Branch & Membership + active-salon resolution — _note: registering a user auto-creates Salon+OWNER Membership (signal); `core.permissions.Role`/`get_active_membership` now wired to the real models; 41 tests passing_
- [x] **1.4** Onboarding wizard (10 steps) + booking slug — _note: single flexible `GET/PATCH /salons/onboarding/` + `POST /salons/onboarding/complete/`; found and fixed a pre-existing bug in `CurrentSalonMixin` (0.2) where permission checks ran before salon resolution; 50 tests passing_

### Phase 2 — Services & catalog
- [x] **2.1** Service categories & services (CRUD, tenant-scoped) — _note: first real use of SalonScopedViewSet + IsSalonMember; cross-tenant FK validation on category/branch; 60 tests passing_
- [x] **2.2** Packages (MVP-light) — _note: `Package`+`PackageService` via nested-writable serializer; read/create only (PATCH/DELETE return 405 by design); 67 tests passing_

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
- 2026-08-18 · `apps/core/permissions.py` defines a placeholder `Role` (plain strings) since `apps.salons.Membership` doesn't exist until Phase 1.3. Replace references with the real `Membership.role` TextChoices once that lands; `get_active_membership()` uses `apps.get_model("salons", "Membership")` for the same reason. — **Resolved 2026-08-18 (Module 1.3):** both now import `apps.salons.models` directly.
- 2026-08-18 · Module 1.3: registration auto-creates a Salon + OWNER Membership via a `post_save` signal on `User` (`apps/salons/signals.py`), not inside `RegisterView` — keeps `apps.accounts` decoupled from `apps.salons`. Superusers are excluded (SaaS Super Admin isn't a salon owner). "Active salon" is `Membership.is_current`, enforced to at most one per user by a Postgres partial unique constraint — chosen over a field on `User` so all tenancy state stays on the Membership row.
- 2026-08-18 · Enabled `rest_framework_simplejwt.token_blacklist` (bundled with the already-approved simplejwt package, not a new dependency) so `/auth/logout/` can actually invalidate a refresh token. Reminder for future auth-adjacent views: the project's `DEFAULT_PERMISSION_CLASSES` is `IsAuthenticated`, so any endpoint that must work *before* login (login itself, token refresh, register) needs an explicit `permission_classes = [AllowAny]` override — see `apps/accounts/views.py`.
- 2026-08-18 · **Bug found & fixed (originated in 0.2):** `SalonScopedViewSet` resolved `request.salon` inside `initial()` *after* calling `super().initial()` — but `super().initial()` already runs `check_permissions()` internally, so `IsSalonMember` always saw an unresolved `request.salon` and would have rejected every request. Never caught earlier because no concrete scoped model/endpoint existed to exercise it until this module's onboarding view. Fixed by moving resolution into `perform_authentication()` (extracted as `CurrentSalonMixin` in `apps/core/views.py`), which DRF calls strictly before `check_permissions()`. Any future non-ModelViewSet endpoint needing salon context should mix in `CurrentSalonMixin`.
- 2026-08-18 · Module 1.4: one flexible `GET/PATCH /api/v1/salons/onboarding/` endpoint covers all 10 wizard steps rather than ten separate routes — each PATCH just sends the fields for whichever step the client is on. `POST .../onboarding/complete/` requires `name` + `slug` to be set. The "services" and "staff" steps have no real data yet (those models don't exist until Phase 2/3) — `Salon.services_step_done`/`staff_step_done` are just acknowledgement flags for the wizard UI until then.
- 2026-08-18 · Module 2.1, two patterns to reuse for every future scoped model with FKs to another scoped model (Staff↔StaffService, Appointment↔Service/Staff, etc.): (1) DRF's automatic `UniqueTogetherValidator` only fires when *every* field in a `Meta.constraints` `UniqueConstraint` is also a serializer field — since `salon` deliberately isn't (it's stamped by `perform_create`, not client-supplied), any `(salon, X)` uniqueness constraint needs an explicit `validate_<field>` doing the same lookup manually, or a duplicate falls through to a raw `IntegrityError` (500) instead of a clean 400. (2) A `PrimaryKeyRelatedField` to another scoped model (e.g. `Service.category`) has an unscoped default queryset, so a client can pass another salon's object id — the child record itself still gets the right `salon` via `perform_create`, but the FK would point cross-tenant. Needs an explicit `validate_<field>` checking `related_obj.salon_id == request.salon.id`. See `apps/catalog/serializers.py`.

## Blockers / open questions
_List anything waiting on the human._