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
- [x] **3.1** Staff profiles + staff-service mapping — _note: first Phase 3+ app built straight with `views.py`/`urls.py` (no DRF baggage to dodge); `Staff.role` is a free-text job title, deliberately separate from `Membership.role` (system permission level) since not every staff member has a login — `Staff.membership` is an optional OneToOne for the ones who do; whole module gated to OWNER/MANAGER via a plain `if` (salary/commission data); `working_hours` is a JSONField placeholder like `Salon.business_hours`, superseded by 3.2's real availability model; added select/textarea/checkbox styles to base.css (first form needing them); 9 tests passing, 75 total_
- [x] **3.2** Staff availability endpoint — _note: replaced 3.1's placeholder `Staff.working_hours` JSONField with a real `StaffWorkingHours` model (one row per weekday, `staff+weekday` unique; missing/off row = not scheduled) — confirmed with the human first since it's a schema change to a previous module (CLAUDE.md §2 rule 8); migration `staff/0002` does `RemoveField` + `CreateModel`, fine since it's dev-only data. `/staff/<id>/hours/` (manager-only, a `modelformset_factory` of exactly 7 fixed rows, auto-provisioned via `get_or_create` on GET) manages the schedule; `/staff/availability/` (GET, service+date query params, open to **any** salon role — not manager-gated like the rest of this module, since it carries no HR data and Phase 5 booking will need it from every role) returns staff who both can perform the service (`StaffService`) and are scheduled that weekday. Deliberately does **not** check existing bookings yet — `Appointment` doesn't exist until Phase 5; CLAUDE.md's 5.2 already earmarks "reuse Phase 3.2 availability" for that conflict layer. 13 staff tests passing, 80 total_

### Phase 4 — Customers (CRM)
- [x] **4.1** Customer profile + history scaffold + search — _note: `apps/crm`, open to every salon role (front-desk/reception is the primary user, unlike the manager-only Staff module); duplicate-mobile guard per salon is both a DB `UniqueConstraint` and a `CustomerForm.clean_mobile()` check (reusing the Module 2.1 lesson: constraint alone means a duplicate 500s as a raw `IntegrityError` instead of a clean form error); `source` is a fixed `TextChoices` on `Customer` itself for MVP, not a separate `LeadSource` model (that's V2's Lead pipeline); the "history" scaffold is `/customers/<id>/` with empty-state Appointments/Payments/Reviews cards, ready for Phase 5/6/V2 to fill in with real querysets; search is a GET `?q=` filtering name-or-mobile. 8 tests passing, 92 total_

### Phase 5 — Appointments (core)
- [x] **5.1** Appointment + AppointmentService + status flow — _note: `apps/scheduling`, open to every salon role (booking is front-desk work, same reasoning as CRM); `Appointment.price`/`duration_minutes` are **derived**, not user-entered — recalculated from `AppointmentService` lines every time services are added/removed (`_recalculate_totals`), while `discount`/`advance`/`notes` stay manual fields; `AppointmentService.price`/`duration_minutes` are snapshotted from the `Service` at add-time so a later price-list edit can't retroactively change a past booking; status transitions are a `VALID_TRANSITIONS` dict on the model (`Appointment.transition_to()`) — BOOKED can skip straight to ARRIVED for walk-ins, PAID/CANCELLED/NO_SHOW are terminal; the services sub-form is a scoped `inlineformset_factory` (custom `AppointmentServiceForm.__init__(salon=...)` + `form_kwargs` — same cross-tenant-FK pattern as 2.1/3.1/4.1, just via formset `form_kwargs` instead of a plain form `__init__`). Deliberately does **not** prevent double-booking a staff member yet — that conflict check is explicitly 5.2's job, reusing 3.2's availability. 11 tests passing, 103 total_
- [x] **5.2** Calendar views, filters & double-booking prevention — _note: `/appointments/` gained `?view=day|week|month&date=YYYY-MM-DD` + `?staff=&service=&branch=&status=` filters (all optional, combinable); prev/next links preserve the active filters. Double-booking check (`_find_staff_conflict` in `apps/scheduling/views.py`) treats an appointment's services as one shared `[time, time+duration_minutes)` window (there's no per-line start time in this schema — see 5.1's note), so "conflict" means the same staff member has two appointments on the same date whose windows overlap; half-open intervals mean back-to-back bookings (one ending exactly when the next starts) are allowed. Checked on both the services-formset save and on editing an appointment's date/time (`_save_and_check_conflicts` wraps the mutation in `transaction.atomic()` + `set_rollback(True)` on conflict, so a rejected change leaves zero trace in the DB). CANCELLED/NO_SHOW appointments are excluded from the conflict check. Does not flag two different lines *within the same appointment* assigned to the same staff — only cross-appointment conflicts, matching the DoD's "double-booking" framing. 8 new tests (day/week/month ranges, staff+status filters, overlap rejected, back-to-back allowed, cancelled ignored, edit-into-conflict rejected), 111 total_

### Phase 6 — Billing / POS
- [x] **6.1** Invoice + items + payment (from completed appointment) — _note: `apps/billing`, open to every salon role (checkout is front-desk work, same reasoning as CRM/Scheduling). One `Invoice` per `Appointment` (`OneToOneField`, generation is a POST-only action gated on `appointment.status == COMPLETED`, idempotent — generating twice just redirects to the existing invoice via `hasattr(appointment, "invoice")`). `InvoiceItem` rows are auto-created from the appointment's `AppointmentService` lines (snapshotting price + the *service's* `tax_percent` from catalog — Phase 2.1's field, unused until now); ad-hoc lines (no `Product` model yet — that's Phase 7) are a manual description/price/tax mini-form on the invoice page, same `service=None` pattern as AppointmentService.staff being optional. `subtotal`/`tax_total`/`total` are stored + recalculated (`_recalculate_invoice`, same pattern as Appointment.price in 5.1) whenever items or discount change; `discount` seeds from `appointment.discount` at generation but is independently editable after. "Split payment" (CLAUDE's payment-methods list) isn't a `Payment.method` value — it's just multiple `Payment` rows against one invoice; recording a payment that brings `paid_total >= total` auto-calls `appointment.transition_to(PAID)` (reuses 5.1's status machine — PAID is only reachable from COMPLETED, so this can't fire early). No delete on Invoice/InvoiceItem/Payment — financial records, not blind CRUD symmetry with the rest of the app. `invoice_number` (`INV-000042`) is a computed property off the pk, not a stored field. 11 tests passing, 122 total_
- [x] **6.2** Expenses — _note: added to `apps/billing` (per CLAUDE.md §4.1's project layout — Expense was always slated for the billing app, not its own), not a new app. `category` is a fixed `TextChoices` (Rent/Utilities/Supplies/Salaries/Marketing/Maintenance/Other). Gated OWNER/MANAGER-only like Staff — bookkeeping, not front-desk work, unlike Customers/Appointments/Billing which are open to every role. Standard full CRUD (list/create/edit/delete), matching the "Simple CRUD" wording in its own DoD (unlike 6.1's specific generate-from-appointment workflow). Nothing reads this yet — feeds `profit = revenue - expenses` once Phase 10 (Reports) exists. 6 new tests, 128 total_

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

- 2026-08-18 · **Architecture pivot: API-first (DRF+JWT) → Django Templates monolith (session auth).** See CLAUDE.md §3/§4 for the full rationale and new conventions. Added: `templates/` (project-wide `base.html`, sidebar+topbar shell) + `static/css/base.css` (design system) + `static/js/forms.js`; `apps/core/decorators.py:salon_member_required` (template-view equivalent of `SalonScopedViewSet`); `apps/accounts/web_views.py`+`web_forms.py`+`web_urls.py` (login/register/logout pages); `apps/salons/web_views.py`+`web_urls.py` (dashboard page — salon + services list). Root `/` now redirects to `/login/`. The Phase 0–2 DRF/JWT code (`serializers.py`, `ModelViewSet`s, `/api/v1/...`) was **not deleted** — see open question below.
- 2026-08-19 · Module 3.1: project's Python venv lives at `d:\projects\salon_saas\.venv` — **one level above** this repo (`salonos/` is the git root and Django project root, but not the venv's parent). It's gitignored from both locations. A prior session missed this, created a redundant second venv inside `salonos/`, and had to delete it. Documented in CLAUDE.md §5 now — check there before assuming no venv exists.
- 2026-08-19 · Module 3.2: confirmed with the human before doing it (CLAUDE.md §2 rule 8, schema change to a previous module) — removed 3.1's placeholder `Staff.working_hours` JSONField and replaced it with a real `StaffWorkingHours` model. Reusable pattern for any future "exactly N fixed rows, no add/delete" form (e.g. a salon's weekly business hours, if that ever moves off `Salon.business_hours` JSON the same way): `modelformset_factory(..., extra=0, can_delete=False)` over a queryset the view has already guaranteed to contain exactly those N rows (via `get_or_create` in a loop keyed on the fixed dimension — weekday here), with that fixed/keying field left out of `fields=[...]` entirely so it's never client-editable, only ever set server-side.

- 2026-08-19 · Added `python manage.py seed_demo_data` (`apps/core/management/commands/`) — a management command, not a `loaddata` fixture, chosen specifically to sidestep two fixture pain points: pre-hashed passwords in JSON, and `loaddata`'s `raw=True` save skipping the `apps.salons` post_save signal's dependency on other already-saved rows. Seeds one demo salon (slug `demo-salon`) with a branch, one login per `Role` (all password `DemoPass123!` — see CLAUDE.md §5 for the full list), a 2-category/4-service catalog, and 3 staff (one linked to the STAFF-role login via `Staff.membership`, demonstrating that optional link from Module 3.1). Idempotent (safe to re-run), `--reset` wipes and rebuilds, refuses to run outside `DEBUG` without `--force`. Already run once against the real dev DB.

## Blockers / open questions
_List anything waiting on the human._

- 2026-08-18 · Should the legacy Phase 0–2 DRF/JWT API (`/api/v1/...`, `serializers.py`, `rest_framework`/`rest_framework_simplejwt` in `INSTALLED_APPS`) be fully removed now that the Django Templates approach is primary, or left in place (current state — dormant, untouched, still passing its own tests)? Left in place by default since deleting tested code isn't reversible and wasn't explicitly asked for.