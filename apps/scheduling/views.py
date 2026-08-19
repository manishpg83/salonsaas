import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.catalog.models import Service
from apps.core.decorators import salon_member_required
from apps.salons.models import Branch
from apps.staff.models import Staff

from .forms import AppointmentForm, AppointmentServiceFormSet
from .models import Appointment, AppointmentService

CALENDAR_VIEWS = ("day", "week", "month")


def _recalculate_totals(appointment):
    totals = appointment.services.aggregate(
        total_price=Sum("price"), total_duration=Sum("duration_minutes")
    )
    appointment.price = totals["total_price"] or Decimal("0.00")
    appointment.duration_minutes = totals["total_duration"] or 0
    appointment.save(update_fields=["price", "duration_minutes"])


def _end_time(start, duration_minutes):
    return (datetime.combine(date.min, start) + timedelta(minutes=duration_minutes)).time()


def _find_staff_conflict(appointment):
    """If any staff member assigned to `appointment`'s service lines is
    already booked elsewhere on the same date with an overlapping time
    window, returns that other AppointmentService line. Else None.

    A single Appointment has one shared [time, time + duration_minutes)
    window for all of its service lines (there's no per-line start time in
    this schema) — so "double-booked" means the same staff member has two
    appointments whose windows overlap, not two lines within the same
    appointment."""
    staff_ids = (
        appointment.services.exclude(staff__isnull=True)
        .values_list("staff_id", flat=True)
        .distinct()
    )
    if not staff_ids:
        return None

    start = appointment.time
    end = _end_time(start, appointment.duration_minutes)

    other_lines = (
        AppointmentService.objects.filter(
            staff_id__in=staff_ids,
            appointment__salon=appointment.salon,
            appointment__date=appointment.date,
        )
        .exclude(appointment=appointment)
        .exclude(appointment__status__in=[Appointment.Status.CANCELLED, Appointment.Status.NO_SHOW])
        .select_related("appointment", "staff")
    )
    for line in other_lines:
        other = line.appointment
        other_end = _end_time(other.time, other.duration_minutes)
        if start < other_end and other.time < end:
            return line
    return None


def _conflict_message(conflict):
    other = conflict.appointment
    return (
        f"{conflict.staff.name} is already booked for {other.customer.name} at "
        f"{other.time.strftime('%H:%M')} on {other.date} — choose a different time or staff member."
    )


def _save_and_check_conflicts(appointment, mutate):
    """Runs `mutate()` (which changes `appointment` and/or its service
    lines) inside a transaction, then checks for staff double-booking.
    Commits and returns None if clear; otherwise rolls back every change
    `mutate()` made and returns the conflicting AppointmentService line."""
    conflict = None
    with transaction.atomic():
        mutate()
        conflict = _find_staff_conflict(appointment)
        if conflict:
            transaction.set_rollback(True)
    return conflict


def _date_range(view, anchor):
    if view == "week":
        start = anchor - timedelta(days=anchor.weekday())
        end = start + timedelta(days=6)
    elif view == "month":
        start = anchor.replace(day=1)
        end = anchor.replace(day=calendar.monthrange(anchor.year, anchor.month)[1])
    else:
        start = end = anchor
    return start, end


def _shift_anchor(view, anchor, direction):
    if view == "week":
        return anchor + timedelta(days=7 * direction)
    if view == "month":
        month_index = anchor.month - 1 + direction
        year = anchor.year + month_index // 12
        month = month_index % 12 + 1
        day = min(anchor.day, calendar.monthrange(year, month)[1])
        return date(year, month, day)
    return anchor + timedelta(days=direction)


@salon_member_required
def appointment_list_view(request):
    view = request.GET.get("view", "day")
    if view not in CALENDAR_VIEWS:
        view = "day"
    try:
        anchor = date.fromisoformat(request.GET.get("date", "")) if request.GET.get("date") else date.today()
    except ValueError:
        anchor = date.today()
    start, end = _date_range(view, anchor)

    staff_id = request.GET.get("staff", "")
    service_id = request.GET.get("service", "")
    branch_id = request.GET.get("branch", "")
    status = request.GET.get("status", "")

    appointments = Appointment.objects.filter(
        salon=request.salon, date__gte=start, date__lte=end
    ).select_related("customer", "branch")
    if staff_id:
        appointments = appointments.filter(services__staff_id=staff_id)
    if service_id:
        appointments = appointments.filter(services__service_id=service_id)
    if branch_id:
        appointments = appointments.filter(branch_id=branch_id)
    if status:
        appointments = appointments.filter(status=status)
    if staff_id or service_id:
        appointments = appointments.distinct()
    appointments = appointments.order_by("date", "time")

    return render(
        request,
        "scheduling/list.html",
        {
            "appointments": appointments,
            "view": view,
            "anchor": anchor,
            "range_start": start,
            "range_end": end,
            "prev_anchor": _shift_anchor(view, anchor, -1),
            "next_anchor": _shift_anchor(view, anchor, 1),
            "staff_members": Staff.objects.filter(salon=request.salon, is_active=True),
            "services": Service.objects.filter(salon=request.salon, is_active=True),
            "branches": Branch.objects.filter(salon=request.salon),
            "statuses": Appointment.Status.choices,
            "selected_staff": staff_id,
            "selected_service": service_id,
            "selected_branch": branch_id,
            "selected_status": status,
        },
    )


@salon_member_required
def appointment_create_view(request):
    if request.method == "POST":
        form = AppointmentForm(request.POST, salon=request.salon)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.salon = request.salon
            appointment.save()
            messages.success(request, "Appointment created — now add its services.")
            return redirect("appointment-services", pk=appointment.pk)
    else:
        form = AppointmentForm(salon=request.salon)

    return render(request, "scheduling/form.html", {"form": form, "appointment": None})


@salon_member_required
def appointment_edit_view(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, salon=request.salon)

    if request.method == "POST":
        form = AppointmentForm(request.POST, instance=appointment, salon=request.salon)
        if form.is_valid():
            conflict = _save_and_check_conflicts(appointment, form.save)
            if conflict:
                messages.error(request, _conflict_message(conflict))
            else:
                messages.success(request, "Appointment updated.")
                return redirect("appointment-detail", pk=appointment.pk)
    else:
        form = AppointmentForm(instance=appointment, salon=request.salon)

    return render(request, "scheduling/form.html", {"form": form, "appointment": appointment})


@require_POST
@salon_member_required
def appointment_delete_view(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, salon=request.salon)
    appointment.delete()
    messages.success(request, "Appointment deleted.")
    return redirect("appointment-list")


@salon_member_required
def appointment_detail_view(request, pk):
    appointment = get_object_or_404(
        Appointment.objects.select_related("customer", "branch"), pk=pk, salon=request.salon
    )
    lines = appointment.services.select_related("service", "staff")
    return render(
        request,
        "scheduling/detail.html",
        {"appointment": appointment, "lines": lines, "next_statuses": appointment.next_statuses()},
    )


@salon_member_required
def appointment_services_view(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, salon=request.salon)

    if request.method == "POST":
        formset = AppointmentServiceFormSet(
            request.POST,
            instance=appointment,
            prefix="services",
            form_kwargs={"salon": request.salon},
        )
        if formset.is_valid():

            def _save_lines():
                for line in formset.save(commit=False):
                    line.salon = request.salon
                    line.price = line.service.price
                    line.duration_minutes = line.service.duration_minutes
                    line.save()
                for line in formset.deleted_objects:
                    line.delete()
                _recalculate_totals(appointment)

            conflict = _save_and_check_conflicts(appointment, _save_lines)
            if conflict:
                messages.error(request, _conflict_message(conflict))
            else:
                messages.success(request, "Services updated.")
                return redirect("appointment-detail", pk=appointment.pk)
    else:
        formset = AppointmentServiceFormSet(
            instance=appointment, prefix="services", form_kwargs={"salon": request.salon}
        )

    return render(
        request, "scheduling/services_form.html", {"formset": formset, "appointment": appointment}
    )


@require_POST
@salon_member_required
def appointment_status_view(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk, salon=request.salon)
    new_status = request.POST.get("status", "")
    try:
        appointment.transition_to(new_status)
    except ValueError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, f"Appointment marked {appointment.get_status_display()}.")
    return redirect("appointment-detail", pk=appointment.pk)
