from django.db import models

from apps.core.models import SalonScopedModel


class MessageTemplate(SalonScopedModel):
    """One editable template per (salon, trigger) — CLAUDE.md §7 Phase 8.1.

    Exactly one row per `Trigger` choice per salon, auto-provisioned by
    `views._ensure_templates` the first time a salon opens the templates
    page (same "fixed dimension, get_or_create per row" pattern as Phase
    3.2's `StaffWorkingHours`). `is_active` lets a salon turn a trigger off
    without losing the wording; Phase 8.2's automatic triggers only fire for
    an active template.
    """

    class Trigger(models.TextChoices):
        BOOKING_CONFIRMATION = "BOOKING_CONFIRMATION", "Booking confirmation"
        APPOINTMENT_REMINDER = "APPOINTMENT_REMINDER", "Appointment reminder"
        FEEDBACK_REQUEST = "FEEDBACK_REQUEST", "Feedback request"
        CANCELLATION_NOTICE = "CANCELLATION_NOTICE", "Cancellation / reschedule notice"

    # Seed wording for auto-provisioned rows — placeholders use Django's own
    # {{ variable }} template syntax since apps.messaging.services renders
    # bodies with django.template.Template.
    DEFAULT_BODIES = {
        Trigger.BOOKING_CONFIRMATION: (
            "Hi {{ customer_name }}, your appointment at {{ salon_name }} is "
            "confirmed for {{ appointment_date }} at {{ appointment_time }}."
        ),
        Trigger.APPOINTMENT_REMINDER: (
            "Hi {{ customer_name }}, reminder: your appointment at "
            "{{ salon_name }} is coming up on {{ appointment_date }} at "
            "{{ appointment_time }}."
        ),
        Trigger.FEEDBACK_REQUEST: (
            "Hi {{ customer_name }}, thanks for visiting {{ salon_name }}! "
            "We'd love to hear your feedback."
        ),
        Trigger.CANCELLATION_NOTICE: (
            "Hi {{ customer_name }}, your appointment at {{ salon_name }} on "
            "{{ appointment_date }} has been cancelled. Let us know if you'd "
            "like to rebook."
        ),
    }

    trigger = models.CharField(max_length=30, choices=Trigger.choices)
    body = models.TextField(
        help_text=(
            "Placeholders: {{ customer_name }}, {{ salon_name }}, "
            "{{ appointment_date }}, {{ appointment_time }}."
        )
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["trigger"]
        constraints = [
            models.UniqueConstraint(
                fields=["salon", "trigger"], name="unique_message_template_per_trigger_per_salon"
            ),
        ]

    def __str__(self):
        return f"{self.get_trigger_display()} ({self.salon})"


class Message(SalonScopedModel):
    """A logged send attempt — every call to
    `apps.messaging.services.send_message` creates exactly one row, whether
    the configured provider reports success or failure. `recipient`/`body`
    are snapshots of what was actually sent, independent of the customer's
    current mobile number or the template's current wording."""

    class Channel(models.TextChoices):
        WHATSAPP = "WHATSAPP", "WhatsApp"

    class Status(models.TextChoices):
        SENT = "SENT", "Sent"
        FAILED = "FAILED", "Failed"

    customer = models.ForeignKey(
        "crm.Customer", on_delete=models.CASCADE, related_name="messages"
    )
    appointment = models.ForeignKey(
        "scheduling.Appointment", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    trigger = models.CharField(max_length=30, choices=MessageTemplate.Trigger.choices)
    channel = models.CharField(max_length=10, choices=Channel.choices, default=Channel.WHATSAPP)
    recipient = models.CharField(max_length=20)
    body = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SENT)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-sent_at"]

    def __str__(self):
        return f"{self.get_channel_display()} to {self.recipient} ({self.get_status_display()})"
