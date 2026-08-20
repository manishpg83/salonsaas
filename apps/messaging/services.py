from django.template import Context, Template

from .models import Message, MessageTemplate
from .providers import get_provider


def render_body(template_body: str, context: dict) -> str:
    # autoescape=False — this renders plain-text WhatsApp messages, not
    # HTML, so a salon/customer name containing "&", "<", "'" etc. must
    # come through literally instead of as HTML entities.
    return Template(template_body).render(Context(context, autoescape=False))


def send_message(*, salon, customer, trigger, body, appointment=None) -> Message:
    """Sends `body` to `customer.mobile` via the configured provider and
    always logs a `Message` row — SENT or FAILED, never raises, so a
    delivery failure never breaks the caller's own transaction (e.g. an
    appointment status change in Phase 8.2)."""
    provider = get_provider()
    try:
        delivered = provider.send(customer.mobile, body)
    except Exception:
        delivered = False

    return Message.objects.create(
        salon=salon,
        customer=customer,
        appointment=appointment,
        trigger=trigger,
        channel=Message.Channel.WHATSAPP,
        recipient=customer.mobile,
        body=body,
        status=Message.Status.SENT if delivered else Message.Status.FAILED,
    )


def appointment_context(appointment) -> dict:
    """Shared render-context builder for every appointment-based trigger
    (Phase 8.2) — one definition instead of duplicating the same four
    placeholders across apps.scheduling's views and the reminders
    management command. Takes any object with the right attributes
    (an Appointment, duck-typed) so this module doesn't need to import
    apps.scheduling and risk a circular import."""
    return {
        "customer_name": appointment.customer.name,
        "salon_name": appointment.salon.name,
        "appointment_date": appointment.date.strftime("%d %b %Y"),
        "appointment_time": appointment.time.strftime("%I:%M %p").lstrip("0"),
    }


def trigger_message(*, salon, customer, trigger, context, appointment=None) -> Message | None:
    """Automatic-trigger entry point (Phase 8.2, as opposed to 8.1's
    explicit `send_message` used by the "send test" action). Auto-provisions
    the (salon, trigger) template with its default wording on first use —
    same effect as visiting /messaging/templates/ first, so a brand new
    salon's very first booking still sends a confirmation without anyone
    needing to configure anything — but returns None without sending (and
    without logging a Message) if the salon has explicitly turned that
    trigger off via `is_active`."""
    template, _created = MessageTemplate.objects.get_or_create(
        salon=salon,
        trigger=trigger,
        defaults={"body": MessageTemplate.DEFAULT_BODIES[trigger]},
    )
    if not template.is_active:
        return None
    body = render_body(template.body, context)
    return send_message(salon=salon, customer=customer, trigger=trigger, body=body, appointment=appointment)
