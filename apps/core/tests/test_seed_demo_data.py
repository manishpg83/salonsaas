import pytest
from django.core.management import call_command

from apps.salons.models import Membership, Role, Salon
from apps.staff.models import Staff, StaffService, StaffWorkingHours

pytestmark = pytest.mark.django_db


def test_seed_demo_data_creates_expected_records():
    call_command("seed_demo_data", force=True)

    salon = Salon.objects.get(slug="demo-salon")
    assert salon.onboarding_completed is True

    roles = set(Membership.objects.filter(salon=salon).values_list("role", flat=True))
    assert roles == {Role.OWNER, Role.MANAGER, Role.RECEPTIONIST, Role.STAFF}

    assert Staff.objects.filter(salon=salon).count() == 3
    assert StaffService.objects.filter(salon=salon).exists()
    assert StaffWorkingHours.objects.filter(salon=salon).count() == 3 * 7

    linked = Staff.objects.get(salon=salon, name="Ritu Singh")
    assert linked.membership is not None
    assert linked.membership.role == Role.STAFF


def test_seed_demo_data_is_idempotent():
    call_command("seed_demo_data", force=True)
    call_command("seed_demo_data", force=True)

    assert Salon.objects.filter(slug="demo-salon").count() == 1
    assert Staff.objects.filter(salon__slug="demo-salon").count() == 3
    assert Membership.objects.filter(salon__slug="demo-salon").count() == 4


def test_seed_demo_data_reset_flag_recreates_cleanly():
    call_command("seed_demo_data", force=True)
    call_command("seed_demo_data", force=True, reset=True)

    assert Salon.objects.filter(slug="demo-salon").count() == 1
    assert Staff.objects.filter(salon__slug="demo-salon").count() == 3


def test_seed_demo_data_refuses_to_run_without_debug_or_force(settings):
    from django.core.management.base import CommandError

    settings.DEBUG = False
    with pytest.raises(CommandError):
        call_command("seed_demo_data")
