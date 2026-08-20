from django.template import Context, Template

from .models import Message
from .providers import get_provider


def render_body(template_body: str, context: dict) -> str:
    return Template(template_body).render(Context(context))


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
