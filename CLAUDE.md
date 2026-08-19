# CLAUDE.md — Salon SaaS ("SalonOS")

> This file is the single source of truth for building this project.
> Claude Code: read this file fully before doing anything. Follow the
> **Operating Rules** exactly. Build **one module at a time** and then **stop**.

---

## 1. What we're building

A multi-tenant SaaS where a salon owner runs their entire business from one
dashboard: customers, leads, appointments, staff, services, inventory, billing,
WhatsApp communication, marketing and analytics.

The full product spec lives in `docs/blueprint.md` (the human will add it).
This CLAUDE.md contains everything you need to build the MVP without the PDF;
use `docs/blueprint.md` only for extra field-level detail when a module is
ambiguous.

**Core product loop (keep this in mind for every feature):**
`Lead → Customer → Appointment → Service → Payment → Review → Re-visit → Marketing → Repeat`

**User roles:** Super Admin (SaaS owner), Salon Owner, Branch Manager,
Receptionist, Staff/Beautician, Customer (booking side).

---

## 2. Operating Rules (read carefully — these are non-negotiable)

1. **One module at a time.** Each phase below is split into numbered modules.
   Build exactly one module, then **STOP and print a short summary** of what you
   did and how to test it. The human will test, commit, and tell you to continue.
2. **Never skip ahead** to a later module or phase, even if it seems trivial.
3. **Do not commit.** The human handles all `git commit` / `git push`. You may
   *suggest* a commit message (see §6).
4. **Migrations always.** Whenever you touch models, generate the migration in
   the same module and mention the command to run it.
5. **Tests always.** Every module ships with tests. A module is not "done"
   without passing tests (see §8, Definition of Done).
6. **Respect multi-tenancy.** Every business model is salon-scoped. Never write
   a query or endpoint that can leak data across salons (see §4.2). This is the
   single most important correctness rule in the project.
7. **Update `PROGRESS.md`** at the end of every module: tick the checkbox and
   add a one-line note.
8. **Ask before large deviations.** If a module needs a design decision not
   covered here (e.g. a new dependency, a schema change to a previous module),
   pause and ask the human first.
9. **Keep it boring and readable.** Prefer clear, conventional Django/DRF code
   over clever abstractions. This is an MVP that real salons will use.
10. **Match existing patterns.** Once a pattern is set in an early module
    (serializers, viewsets, permissions, tests), reuse it everywhere.

At the start of every session, read `PROGRESS.md` first to see where we are.

---

## 3. Tech stack

| Layer          | Choice                                                        |
|----------------|---------------------------------------------------------------|
| Language       | Python 3.12+                                                   |
| Framework      | Django 5.x                                                     |
| UI             | Django Templates — server-rendered HTML (monolith, no SPA)    |
| Auth           | Django's built-in session auth (`django.contrib.auth`)        |
| Database       | PostgreSQL 15+                                                 |
| DB driver      | psycopg[binary]                                                |
| Config         | django-environ (all secrets via `.env`, never hardcoded)      |
| CORS           | django-cors-headers                                           |
| Testing        | pytest, pytest-django, factory_boy                            |
| Async (later)  | Celery + Redis + django-celery-beat (introduced in Phase 8)   |
| Payments (later)| Razorpay                                                     |
| WhatsApp (later)| WhatsApp Cloud API (Meta) — abstracted behind a provider     |

> **BLUEPRINT STACK OVERRIDE.** `docs/blueprint.md` (section 32) recommends
> Next.js + Node/NestJS + Supabase. **Ignore that backend recommendation.**
> This project's backend is **Django + PostgreSQL**, and this table is the
> single authoritative stack. The blueprint's *non-backend* choices still stand
> and map cleanly onto Django: PostgreSQL (identical), Razorpay, WhatsApp Cloud
> API, Resend/SES email, and S3 storage (via `django-storages`). Auth is
> Django's own session auth (not Supabase Auth, not JWT).

> **ARCHITECTURE PIVOT (2026-08-18).** Phases 0–2 were built API-first with
> Django REST Framework + `djangorestframework-simplejwt` (JWT). We've since
> switched to a **Django Templates monolith**: server-rendered HTML pages,
> session-based auth, `Form`/`ModelForm` instead of serializers. **From Phase 3
> onward, every module is built this way** — see §4.2–§4.4 for the
> template-era conventions.
>
> The Phase 0–2 DRF/JWT code (`rest_framework`, `rest_framework_simplejwt`,
> every `serializers.py`, every `ModelViewSet`, the `/api/v1/...` routes) has
> **not been deleted** — deleting six modules of tested, working code isn't
> reversible, and wasn't asked for. It still exists, still has passing tests,
> and still technically works, but it is no longer the primary interface and
> is not maintained going forward. Don't add DRF endpoints to new modules
> unless explicitly asked. `djangorestframework` and
> `djangorestframework-simplejwt` stay in `requirements.txt` for that reason.

Do **not** add dependencies beyond this table without asking. When a phase needs
a new one, it is called out in that phase.

---

## 4. Architecture & conventions

### 4.1 Project layout

Django project named `config`, apps split by domain. Use this exact layout:

```
salonos/
├── config/                 # project: settings, urls, wsgi/asgi, celery
│   └── settings/
│       ├── base.py
│       ├── dev.py
│       └── prod.py
├── apps/
│   ├── core/               # base models, mixins, tenancy, shared utils
│   ├── accounts/           # User, auth, OTP, login/register/logout pages
│   ├── salons/             # Salon, Branch, onboarding, Membership, Role, dashboard page
│   ├── catalog/            # Service, ServiceCategory, Package, Membership plans
│   ├── staff/              # Staff, StaffService, availability, attendance, commission
│   ├── crm/                # Customer, CustomerHistory, Lead, LeadSource
│   ├── scheduling/         # Appointment, AppointmentService, status flow
│   ├── inventory/          # Product, Supplier, Purchase, StockTransaction
│   ├── billing/            # Invoice, InvoiceItem, Payment, Expense
│   ├── messaging/          # MessageTemplate, Message, WhatsApp provider
│   ├── reports/            # aggregation/report endpoints (read-only)
│   ├── dashboard/          # dashboard aggregation endpoints (read-only)
│   └── subscriptions/      # SaaS plans, salon subscriptions (super admin)
├── templates/               # project-wide: base.html (sidebar+topbar shell)
├── static/
│   ├── css/                 # base.css — shared design system
│   └── js/                  # small vanilla-JS polish (no build step, no framework)
├── docs/
│   └── blueprint.md
├── tests/                  # optional cross-app tests; app tests live in each app
├── manage.py
├── pytest.ini
├── requirements.txt
├── .env.example
├── .gitignore
├── PROGRESS.md
└── CLAUDE.md
```

**From Phase 3 onward**, every app has: `models.py`, `views.py` (Django views —
function-based unless a module clearly wants class-based), `forms.py`
(`Form`/`ModelForm`), `urls.py`, `admin.py`, `tests/`, `migrations/`, and its
own `templates/<app_label>/*.html` (list page, create/edit form page — Django's
convention of namespacing templates under the app's label avoids collisions
between apps). Phase 0–2 apps additionally still carry `serializers.py` and a
DRF `views.py`/`urls.py` from before the pivot — untouched, not a pattern to
copy for new work. Since `accounts` and `salons` already had a DRF
`views.py`/`urls.py` when the pivot happened, their new template views live
in parallel `web_views.py`/`web_urls.py` files instead of colliding with the
existing ones. Apps started fresh from Phase 3 onward don't have that
baggage — just use `views.py`/`urls.py` directly for template views.

### 4.2 Multi-tenancy (the most important rule)

Strategy: **shared database, shared schema, row-level scoping by `salon`.**

- `apps/core/models.py` defines two abstract base models:
  - `TimeStampedModel` → `created_at`, `updated_at` (auto).
  - `SalonScopedModel(TimeStampedModel)` → adds
    `salon = ForeignKey('salons.Salon', on_delete=CASCADE, related_name='+')`
    and a default manager that can filter by salon.
- **Every business model inherits `SalonScopedModel`** (Customer, Appointment,
  Service, Product, Invoice, etc.). The only models that are *not* salon-scoped:
  `User`, `Salon`, `Role`, `SubscriptionPlan`, and Super-Admin models.
- Resolve the "current salon" from the authenticated user's active `Membership`,
  via `apps.core.salon_context.get_active_membership(user)`.
- **Template views (Phase 3+):** decorate the view with
  `apps.core.decorators.salon_member_required`, which wraps Django's
  `login_required`, then sets `request.membership`/`request.salon` before the
  view body runs. Every template view that touches a scoped model uses this
  decorator and filters its queryset by `salon=request.salon` explicitly —
  there's no automatic queryset-filtering magic like the old viewset had, so
  **never** query a scoped model without that explicit filter.
- **DRF views (Phase 0–2, legacy):** `SalonScopedViewSet` in `apps/core/views.py`
  filters `get_queryset()` to `request.salon` and auto-sets `salon=request.salon`
  on create. Still there, still correct, just not how new modules are built.
- Write a reusable test helper that asserts salon A cannot read/write salon B's
  objects. Every scoped module must include a cross-tenant isolation test.

### 4.3 Roles & permissions

- `Role` choices for MVP (on the `Membership` model, not per-object):
  `OWNER`, `MANAGER`, `RECEPTIONIST`, `STAFF`. Super Admin = Django
  `is_superuser` on `User`.
- A `Membership` model links `User ↔ Salon ↔ Role (+ optional Branch)`. A user
  can belong to multiple salons; the active salon is chosen at login/context.
- **Template views (Phase 3+):** role checks are a plain `if` at the top of the
  view body (e.g. `if request.membership.role not in (Role.OWNER, Role.MANAGER): raise PermissionDenied`),
  not a class-based permission system — there's no DRF permission pipeline to
  hook into anymore. Keep it role-based for MVP; granular per-action
  permissions are still a Version 2 concern.
- **DRF views (Phase 0–2, legacy):** permission classes in
  `apps/core/permissions.py` — `IsOwner`, `IsOwnerOrManager`, `IsSalonMember`.
  Still there, not the pattern for new work.

### 4.4 Template & form conventions

- Pages are plain Django views (function-based unless a module clearly wants
  class-based) returning `render(request, "app_label/page.html", context)`.
- Forms: `django.forms.Form`/`ModelForm`, explicit `fields` (never `fields =
  "__all__"` on a `ModelForm`), matching the old "no `fields = '__all__'`"
  rule from the API era.
- Every list page needs a matching create page; edit reuses the same form
  template where practical. Deletes are a POST-only action (a button in a
  small `<form>`, not a bare link) — never a GET, since GET must stay
  side-effect-free.
- Cross-tenant FK choices: when a form field references another scoped model
  (e.g. a Service form's `category` dropdown), restrict the field's queryset
  to `request.salon` in the view/form `__init__`, the same way the old DRF
  serializers validated `validate_<field>` — a client (or a malicious POST)
  must not be able to attach an object from another salon.
- Success/error feedback via `django.contrib.messages`, rendered in
  `base.html`. Field errors render inline via `{{ field.errors }}`.
- Money: `DecimalField(max_digits=12, decimal_places=2)`, consistent
  everywhere (unchanged from the API era).
- Enums: Django `TextChoices` (unchanged).
- Timestamps: `USE_TZ = True`, store UTC (unchanged).
- **DRF views (Phase 0–2, legacy):** still live under `/api/v1/...` with
  serializers, `ModelViewSet` + routers, `PageNumberPagination` (page size
  20). Untouched; not how new endpoints get built.

### 4.5 Naming

- Models singular PascalCase (`Customer`). DB tables default.
- Template page URLs plural where the page is a list, singular action verbs
  for forms (`/services/`, `/services/new/`, `/services/<id>/edit/`).
  Legacy DRF endpoints keep their existing `/api/v1/customers/`-style paths.
- Conventional commits for suggested messages (`feat:`, `fix:`, `chore:`,
  `test:`, `docs:`).

---

## 5. Commands

```bash
# setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# db
python manage.py makemigrations
python manage.py migrate

# run
python manage.py runserver

# tests
pytest -q

# create super admin (SaaS owner)
python manage.py createsuperuser
```

Settings module for local dev: `config.settings.dev`
(set `DJANGO_SETTINGS_MODULE=config.settings.dev`).

---

## 6. Git & workflow

- The **human commits after every module.** You never run git.
- At the end of each module, print:
  1. a bullet summary of files added/changed,
  2. the exact commands to run migrations + tests,
  3. a suggested commit message, e.g.
     `feat(crm): add Customer model, CRUD API and tenant-scoping tests`
- One module ≈ one commit. Keep modules small enough to review in one sitting.

---

## 7. Build plan

Legend: each **Module** = one build-then-stop unit. Fields are the minimum; see
`docs/blueprint.md` for the full list. Reorder inside a module only if needed.

> NOTE: This ordering is dependency-driven. It differs slightly from the
> blueprint's MVP list (Dashboard is built late because it aggregates data from
> other modules that must exist first).

> NOTE: Phases 0–2 below describe what was actually built at the time — DRF
> endpoints, serializers, JWT. Left as historical record, not edited after the
> fact. **From Phase 3 onward, wherever a module description below says
> "CRUD" or "endpoints," read that as: a list page, a create/edit form page
> (Django `ModelForm`), and a delete action — server-rendered templates per
> §4.4, not a DRF API.** Every such module also ships whatever `templates/`
> pages it needs, styled with the shared `static/css/base.css`.

---

### PHASE 0 — Foundation & setup

**0.1 Project bootstrap**
Create venv, `requirements.txt`, Django project `config`, split settings
(base/dev/prod), `.env.example` + `django-environ`, PostgreSQL connection,
`django-cors-headers`, DRF + SimpleJWT configured, `apps/` package, `pytest.ini`,
`.gitignore`, empty `PROGRESS.md` (with the module checklist copied from §7),
and a `/api/v1/health/` endpoint returning `{"status":"ok"}`.
DoD: server runs, health endpoint works, `pytest` runs (1 passing test).

**0.2 Core app (base models + tenancy + permissions skeleton)**
`apps/core`: `TimeStampedModel`, `SalonScopedModel`, `SalonScopedViewSet`,
current-salon resolution, base permission classes, and a reusable
cross-tenant test helper. No user-facing endpoints yet.
DoD: importable base classes + unit tests for the scoping helper.

---

### PHASE 1 — Auth & onboarding

**1.1 Custom user + JWT auth**
`apps/accounts`: custom `User` (email as login, no username), registration,
login (email+password → JWT access/refresh), refresh, logout, `/me/`.
DoD: register + login flow works end-to-end; tests cover happy + bad-password.

**1.2 OTP login + forgot/reset password**
OTP request/verify (mobile or email; for MVP log the OTP to console via a
pluggable sender — real SMS/email is wired later). Forgot-password + reset flow.
DoD: OTP and reset flows tested with the console sender.

**1.3 Salon, Branch & Membership**
`apps/salons`: `Salon`, `Branch`, `Role`, `Membership`. On registration or first
login, create the owner's `Membership`. Endpoints to read the current user's
salons and switch active salon.
DoD: a new owner gets a salon + owner membership; tenancy resolves from it.

**1.4 Onboarding wizard**
Endpoints to complete the 10-step onboarding (name, logo, address, contact,
business hours, services, staff, payment methods, WhatsApp, booking-page slug)
and a `onboarding_completed` flag on `Salon`. Booking slug like
`yourbrand` for `yourbrand.salonapp.com` (store slug only; hosting later).
DoD: wizard can be completed; salon marked ready.

---

### PHASE 2 — Services & catalog

**2.1 Service categories & services**
`apps/catalog`: `ServiceCategory`, `Service` (name, category, price, duration,
description, tax %, gender, branch, active). Salon-scoped CRUD.
DoD: CRUD + tenant-isolation test.

**2.2 Packages (MVP-light)**
`Package` + `PackageService` (services included, package price). Read/create
only for MVP; usage-tracking is V2 — keep it minimal here.
DoD: create a package bundling services; tests.

> Membership plans (Gold etc.) are **V2** — do not build now.

---

### PHASE 3 — Staff

**3.1 Staff profiles + staff-services**
`apps/staff`: `Staff` (name, photo, mobile, role, branch, joining date, salary,
commission %, working hours) linked to a `User`/`Membership` where relevant, and
`StaffService` (which services a staff can perform). Salon-scoped CRUD.
DoD: CRUD, staff↔service mapping, tenant test.

**3.2 Staff availability**
Working-hours model + an availability endpoint that, given a service + date,
returns which staff are free (used later by appointments).
DoD: availability endpoint returns correct free staff for a day.

> Attendance and commission are **V2** — skip for MVP.

---

### PHASE 4 — Customers (CRM)

**4.1 Customer profile + history**
`apps/crm`: `Customer` (name, mobile, email, gender, DOB, anniversary, address,
source, notes). Salon-scoped CRUD, search by name/mobile, duplicate-mobile guard
per salon. Expose a read-only "history" endpoint scaffold (appointments,
payments, reviews) that fills in as those modules land.
DoD: CRUD + search + tenant test.

> Auto-segmentation (VIP, inactive, etc.) and Lead pipeline are **V2** — not now.

---

### PHASE 5 — Appointments (core)

**5.1 Appointment model + status flow**
`apps/scheduling`: `Appointment` (customer, branch, date, time, duration, price,
discount, advance, notes) + `AppointmentService` line items (service + staff).
Status enum: `BOOKED → CONFIRMED → ARRIVED → IN_SERVICE → COMPLETED → PAID`
plus `CANCELLED`, `NO_SHOW`. Enforce valid transitions.
DoD: create appointment with one/more services; status transition endpoint with
validation; tenant test.

**5.2 Calendar & conflict rules**
List endpoints with day/week/month + filters (staff, service, branch, status).
Prevent double-booking the same staff at overlapping times. Reuse Phase 3.2
availability.
DoD: overlapping booking is rejected; filters work; tests for conflicts.

---

### PHASE 6 — Billing / POS

**6.1 Invoice + items + payment**
`apps/billing`: `Invoice`, `InvoiceItem` (services + ad-hoc products), `Payment`.
Generate an invoice from a completed appointment; compute subtotal, discount,
GST/tax, total. Payment methods: cash, UPI, card, bank, online, split.
Marking fully paid moves the appointment to `PAID`.
DoD: bill an appointment end-to-end; totals correct; split payment sums to total;
tests.

**6.2 Expenses**
`Expense` (category from a fixed list, amount, date, note). Simple CRUD. This
enables profit = revenue − expenses later in reports.
DoD: CRUD + tenant test.

---

### PHASE 7 — Basic inventory

**7.1 Products & suppliers**
`apps/inventory`: `Supplier`, `ProductCategory`, `Product` (SKU, category,
supplier, purchase/selling price, current stock, min stock, expiry), `Purchase`
+ `PurchaseItem`, and a `StockTransaction` ledger (IN/OUT/ADJUST).
DoD: create products, record a purchase (stock IN), manual adjust; low-stock flag
via `current_stock <= min_stock`; tests.

**7.2 Service → stock consumption**
Optional per-service consumption recipe (product + qty). When an appointment is
completed, decrement stock via `StockTransaction` (OUT). Keep it simple and
idempotent (don't double-deduct).
DoD: completing a service reduces stock exactly once; tests.

---

### PHASE 8 — WhatsApp transactional notifications

New deps this phase: `celery`, `redis`, `django-celery-beat`. Ask before adding.

**8.1 Messaging provider + templates**
`apps/messaging`: `MessageTemplate`, `Message` (log), and a provider interface
with a `ConsoleProvider` (prints/logs) so nothing external is required to test.
Real WhatsApp Cloud API provider is a config swap.
DoD: sending a message logs it via the console provider; tests.

**8.2 Transactional triggers**
On booking → confirmation; 1 day before → reminder (scheduled via Celery beat);
after completion → feedback request. Cancellation/reschedule → notice.
Wire triggers to Phase 5/6 events.
DoD: booking creates a confirmation Message; reminder task schedules correctly;
tests use the console provider (no live API).

> Marketing campaigns & automations are **V2** — not now.

---

### PHASE 9 — Dashboard

**9.1 Dashboard aggregations**
`apps/dashboard`: read-only endpoints for top cards (today's revenue, today's
appointments, new customers, pending payments, low stock), today's schedule,
revenue over today/week/month/custom range, and insight deltas vs previous
period. All salon-scoped and computed from Phases 4–8.
DoD: numbers match seeded test data; tenant test; performance-sane queries
(use aggregation, avoid N+1).

---

### PHASE 10 — Reports

**10.1 Core reports**
`apps/reports`: read-only endpoints for sales (daily/weekly/monthly, and
by staff/service), customers (new/repeat), appointments
(completed/cancelled/no-show), and inventory (stock value, low stock). CSV
export for each.
DoD: reports return correct aggregates on seeded data; CSV export works; tests.

---

### MVP COMPLETE ✅ — after Phase 10, stop and get real salon feedback.

---

### VERSION 2 (build only after MVP feedback — do NOT start unprompted)

Lead CRM & pipeline · customer auto-segmentation · WhatsApp marketing campaigns
& automations · membership plans · package usage tracking · staff attendance &
commission · supplier/advanced inventory · reviews & feedback · public booking
website + widget · granular per-action permissions.

### VERSION 3

AI business assistant · AI campaign/copy generator · multi-branch rollup ·
advanced analytics · churn/profit prediction · automated reactivation ·
white-label · Super Admin panel & SaaS subscription billing (Razorpay).

---

## 8. Definition of Done (every module)

A module is done only when **all** are true:

- [ ] Models + migrations created; `migrate` runs cleanly.
- [ ] Views + templates implemented (list page, create/edit form) — or, for
      Phase 0–2 legacy modules only, serializers + DRF viewset under `/api/v1/`.
- [ ] Salon scoping enforced (if it's a business model) — `salon_member_required`
      + explicit `salon=request.salon` filtering for template views.
- [ ] Permissions applied (correct roles allowed/denied).
- [ ] Tests written and passing: happy path, validation error, **and** a
      cross-tenant isolation test for scoped models.
- [ ] `admin.py` registered (helps manual QA).
- [ ] `PROGRESS.md` updated with the ticked box + one-line note.
- [ ] Summary + suggested commit message printed for the human.

---

## 9. Definition of the first thing to do

When the human says "start", begin with **Module 0.1** only, then stop.
Do not proceed to 0.2 until told.

---

## 10. Guardrails / do-not-list

- Do **not** hardcode secrets — everything via `.env`.
- Do **not** use `fields = '__all__'` on writable serializers.
- Do **not** add packages outside §3 without asking.
- Do **not** build Version 2 / Version 3 features during the MVP.
- Do **not** commit, push, or rewrite git history.
- Do **not** write a query on a scoped model that bypasses `SalonScopedViewSet`.
- Do **not** proceed to the next module automatically.