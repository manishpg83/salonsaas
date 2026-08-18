import random
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.utils.module_loading import import_string

from .models import OTP

OTP_LENGTH = 6
OTP_TTL_MINUTES = 10


class ConsoleOTPSender:
    """MVP delivery: print the code to the console. Real SMS/email is a
    settings.OTP_SENDER_CLASS swap — no call site changes needed (same
    pattern Phase 8's messaging provider will formalize project-wide)."""

    def send(self, *, user, code, purpose):
        print(f"[OTP] {purpose} code for {user.email}: {code}")


def get_otp_sender():
    sender_class = import_string(
        getattr(settings, "OTP_SENDER_CLASS", "apps.accounts.otp.ConsoleOTPSender")
    )
    return sender_class()


def generate_otp(user, purpose):
    code = f"{random.randint(0, 10 ** OTP_LENGTH - 1):0{OTP_LENGTH}d}"
    otp = OTP.objects.create(
        user=user,
        code=code,
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=OTP_TTL_MINUTES),
    )
    get_otp_sender().send(user=user, code=code, purpose=purpose)
    return otp


def consume_valid_otp(*, email, code, purpose):
    """Look up a matching, unused, unexpired OTP and mark it used. Returns
    None if no such OTP exists — callers can't tell whether the email or the
    code was wrong, which is intentional (CLAUDE.md-style: don't leak which
    part of the credential pair was invalid)."""
    otp = (
        OTP.objects.select_related("user")
        .filter(
            user__email=email,
            code=code,
            purpose=purpose,
            used_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .order_by("-created_at")
        .first()
    )
    if otp:
        otp.used_at = timezone.now()
        otp.save(update_fields=["used_at"])
    return otp
