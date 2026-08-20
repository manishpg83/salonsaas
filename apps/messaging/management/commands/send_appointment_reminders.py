from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.messaging.models import Message, MessageTemplate
from apps.messaging.services import appointment_context, trigger_message
from apps.scheduling.models import Appointment

# Terminal-ish statuses where a reminder no longer makes sense — the visit
# either isn't happening (CANCELLED/NO_SHOW) or has already happened
# (COMPLETED/PAID, which would only occur here for a same-day walk-in whose
# date field still matches "tomorrow" from an odd edit).
SKIP_STATUSES = [
    Appointment.Status.CANCELLED,
    Appointment.Status.NO_SHOW,
    Appointment.Status.COMPLETED,
    Appointment.Status.PAID,
]


class Command(BaseCommand):
    """Sends an APPOINTMENT_REMINDER message for every appointment scheduled
    for tomorrow that hasn't already gotten one (CLAUDE.md §7 Phase 8.2).

    Meant to run once a day via the OS scheduler (Windows Task Scheduler
    locally, cron/systemd-timer in prod) rather than Celery beat — see
    PROGRESS.md's decisions log for why: no new services (Redis, a worker)
    are needed for a once-a-day job, and Celery's worker doesn't run in its
    default prefork pool on Windows. Revisit once real deployment infra
    exists. Safe to run more than once a day: idempotent via the Message log
    (skips an appointment that already has a REMINDER message), not a
    separate "reminder_sent" flag.
    """

    help = "Send WhatsApp reminders for appointments happening tomorrow."

    def handle(self, *args, **options):
        tomorrow = timezone.localdate() + timedelta(days=1)
        appointments = (
            Appointment.objects.filter(date=tomorrow)
            .exclude(status__in=SKIP_STATUSES)
            .select_related("customer", "salon")
        )

        sent = 0
        for appointment in appointments:
            already_reminded = Message.objects.filter(
                appointment=appointment, trigger=MessageTemplate.Trigger.APPOINTMENT_REMINDER
            ).exists()
            if already_reminded:
                continue
            message = trigger_message(
                salon=appointment.salon,
                customer=appointment.customer,
                trigger=MessageTemplate.Trigger.APPOINTMENT_REMINDER,
                context=appointment_context(appointment),
                appointment=appointment,
            )
            if message is not None:
                sent += 1

        self.stdout.write(self.style.SUCCESS(f"Sent {sent} reminder(s) for {tomorrow}."))
