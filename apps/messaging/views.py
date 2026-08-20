from django.contrib import messages as django_messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.decorators import salon_member_required
from apps.salons.models import Role

from .forms import MessageTemplateForm, SendTestMessageForm
from .models import Message, MessageTemplate
from .services import render_body, send_message


def _require_manager(request):
    """Template wording/configuration is business setup, not front-desk
    work — same reasoning (and pattern) as apps/staff and Expenses."""
    if request.membership.role not in (Role.OWNER, Role.MANAGER):
        raise PermissionDenied


def _ensure_templates(salon):
    """Auto-provision one row per Trigger choice the first time a salon's
    templates are viewed — same get_or_create-per-fixed-dimension pattern
    as Phase 3.2's StaffWorkingHours."""
    for trigger, _label in MessageTemplate.Trigger.choices:
        MessageTemplate.objects.get_or_create(
            salon=salon,
            trigger=trigger,
            defaults={"body": MessageTemplate.DEFAULT_BODIES[trigger]},
        )


@salon_member_required
def template_list_view(request):
    _require_manager(request)
    _ensure_templates(request.salon)
    templates = MessageTemplate.objects.filter(salon=request.salon)
    return render(request, "messaging/template_list.html", {"templates": templates})


@salon_member_required
def template_edit_view(request, trigger):
    _require_manager(request)
    _ensure_templates(request.salon)
    template = get_object_or_404(MessageTemplate, salon=request.salon, trigger=trigger)

    if request.method == "POST":
        form = MessageTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            django_messages.success(request, "Template updated.")
            return redirect("message-template-list")
    else:
        form = MessageTemplateForm(instance=template)

    test_form = SendTestMessageForm(salon=request.salon)
    return render(
        request,
        "messaging/template_form.html",
        {"form": form, "template": template, "test_form": test_form},
    )


@require_POST
@salon_member_required
def template_send_test_view(request, trigger):
    _require_manager(request)
    template = get_object_or_404(MessageTemplate, salon=request.salon, trigger=trigger)
    form = SendTestMessageForm(request.POST, salon=request.salon)
    if form.is_valid():
        customer = form.cleaned_data["customer"]
        context = {
            "customer_name": customer.name,
            "salon_name": request.salon.name,
            "appointment_date": "25 Aug 2026",
            "appointment_time": "5:00 PM",
        }
        body = render_body(template.body, context)
        send_message(salon=request.salon, customer=customer, trigger=template.trigger, body=body)
        django_messages.success(request, f"Test message sent to {customer.name}.")
    else:
        django_messages.error(request, "Pick a customer to send the test to.")
    return redirect("message-template-edit", trigger=trigger)


@salon_member_required
def message_log_view(request):
    log = Message.objects.filter(salon=request.salon).select_related("customer")
    return render(request, "messaging/log.html", {"log": log})
