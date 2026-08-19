from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import Service, ServiceCategory
from apps.salons.models import Branch, Membership, Role, Salon
from apps.staff.models import Staff, StaffService, StaffWorkingHours, WeekDay

User = get_user_model()

DEMO_SALON_SLUG = "demo-salon"
DEMO_PASSWORD = "DemoPass123!"

# One login per Role, so manual QA can exercise every role-gated view
# (e.g. RECEPTIONIST getting a 403 on the staff module).
LOGIN_ROLES = [
    ("owner@demo.salonos.test", "Demo Owner", Role.OWNER),
    ("manager@demo.salonos.test", "Demo Manager", Role.MANAGER),
    ("reception@demo.salonos.test", "Demo Receptionist", Role.RECEPTIONIST),
    ("stylist@demo.salonos.test", "Demo Staff", Role.STAFF),
]

# (name, job title, mobile, service names they perform, login email to link
# as their Membership — None for staff with no login of their own).
STAFF_SPECS = [
    ("Priya Sharma", "Senior Stylist", "9111111111", ["Haircut", "Hair Color"], None),
    ("Anjali Verma", "Beautician", "9222222222", ["Facial", "Cleanup"], None),
    ("Ritu Singh", "Junior Stylist", "9333333333", ["Haircut"], "stylist@demo.salonos.test"),
]


class Command(BaseCommand):
    help = (
        "Seeds one demo salon with a branch, one login per role, a service "
        "catalog, and staff (with service mappings + working hours) for "
        "manual QA. Safe to re-run — everything is get_or_create/update_or_create."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete the existing demo salon (and everything scoped to it) before reseeding.",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Allow running even when DEBUG=False.",
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError(
                "Refusing to seed fake demo data with DEBUG=False. Pass --force to override."
            )

        if options["reset"]:
            deleted, _ = Salon.objects.filter(slug=DEMO_SALON_SLUG).delete()
            if deleted:
                self.stdout.write(self.style.WARNING("Deleted existing demo salon."))

        with transaction.atomic():
            salon = self._seed_salon()
            branch = self._seed_branch(salon)
            memberships = self._seed_logins(salon)
            services = self._seed_catalog(salon)
            self._seed_staff(salon, branch, services, memberships)

        self.stdout.write(self.style.SUCCESS(f"Demo salon ready: {salon.name} (slug={salon.slug})"))
        self.stdout.write("Logins (all share the same password):")
        for email, _full_name, role in LOGIN_ROLES:
            self.stdout.write(f"  {email} / {DEMO_PASSWORD}  [{role}]")

    def _seed_salon(self):
        salon, _ = Salon.objects.get_or_create(
            slug=DEMO_SALON_SLUG,
            defaults={
                "name": "Glow & Co. Salon",
                "address": "12 MG Road, Bengaluru",
                "contact_phone": "9800000000",
                "contact_email": "hello@glowandco.test",
                "business_hours": {"mon-sat": "09:00-20:00", "sun": "closed"},
                "payment_methods": ["cash", "upi", "card"],
                "whatsapp_number": "9800000000",
                "services_step_done": True,
                "staff_step_done": True,
                "onboarding_completed": True,
            },
        )
        return salon

    def _seed_branch(self, salon):
        branch, _ = Branch.objects.get_or_create(
            salon=salon,
            name="Main Branch",
            defaults={"address": "12 MG Road, Bengaluru", "phone": "9800000000"},
        )
        return branch

    def _seed_logins(self, salon):
        """Creates (or reuses) one User per LOGIN_ROLES entry and gives each
        a Membership on the demo salon. A newly-created User always gets its
        own personal Salon + OWNER Membership first (apps.salons' signal —
        real self-serve signup behaviour) — for these demo logins we want
        them all sharing *this* salon instead, so we drop whatever stray
        salon the signal made and point their Membership at the demo salon."""
        memberships = {}
        for email, full_name, role in LOGIN_ROLES:
            user = User.objects.filter(email=email).first()
            if user is None:
                user = User.objects.create_user(
                    email=email, full_name=full_name, password=DEMO_PASSWORD
                )

            stray_salon_ids = list(
                Membership.objects.filter(user=user)
                .exclude(salon=salon)
                .values_list("salon_id", flat=True)
            )
            if stray_salon_ids:
                Salon.objects.filter(pk__in=stray_salon_ids).delete()

            membership, _ = Membership.objects.update_or_create(
                user=user, salon=salon, defaults={"role": role, "is_current": True}
            )
            memberships[email] = membership
        return memberships

    def _seed_catalog(self, salon):
        hair, _ = ServiceCategory.objects.get_or_create(salon=salon, name="Hair")
        skin, _ = ServiceCategory.objects.get_or_create(salon=salon, name="Skin")

        service_specs = [
            (hair, "Haircut", "500.00", 30),
            (hair, "Hair Color", "1500.00", 90),
            (skin, "Facial", "1200.00", 60),
            (skin, "Cleanup", "800.00", 40),
        ]
        services = {}
        for category, name, price, duration in service_specs:
            service, _ = Service.objects.get_or_create(
                salon=salon,
                name=name,
                defaults={"category": category, "price": price, "duration_minutes": duration},
            )
            services[name] = service
        return services

    def _seed_staff(self, salon, branch, services, memberships):
        for name, role, mobile, service_names, login_email in STAFF_SPECS:
            staff, _ = Staff.objects.get_or_create(
                salon=salon,
                name=name,
                defaults={
                    "branch": branch,
                    "mobile": mobile,
                    "role": role,
                    "joining_date": "2025-01-01",
                    "salary": "20000",
                    "commission_percent": "10",
                    "membership": memberships.get(login_email) if login_email else None,
                },
            )
            for service_name in service_names:
                StaffService.objects.get_or_create(
                    salon=salon, staff=staff, service=services[service_name]
                )
            for weekday, _label in WeekDay.choices:
                is_sunday = weekday == WeekDay.SUNDAY
                StaffWorkingHours.objects.update_or_create(
                    salon=salon,
                    staff=staff,
                    weekday=weekday,
                    defaults={
                        "is_off": is_sunday,
                        "start_time": None if is_sunday else "09:00",
                        "end_time": None if is_sunday else "18:00",
                    },
                )
