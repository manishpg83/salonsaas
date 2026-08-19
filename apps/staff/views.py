from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.decorators import salon_member_required
from apps.salons.models import Role

from .forms import StaffForm, StaffServicesForm
from .models import Staff, StaffService


def _require_manager(request):
    """Staff records carry salary/commission — restrict the whole module to
    OWNER/MANAGER, same as CLAUDE.md §4.3's plain-if pattern."""
    if request.membership.role not in (Role.OWNER, Role.MANAGER):
        raise PermissionDenied


@salon_member_required
def staff_list_view(request):
    _require_manager(request)
    staff = Staff.objects.filter(salon=request.salon).select_related("branch")
    return render(request, "staff/list.html", {"staff": staff})


@salon_member_required
def staff_create_view(request):
    _require_manager(request)
    if request.method == "POST":
        form = StaffForm(request.POST, salon=request.salon)
        if form.is_valid():
            staff = form.save(commit=False)
            staff.salon = request.salon
            staff.save()
            messages.success(request, f"{staff.name} added.")
            return redirect("staff-list")
    else:
        form = StaffForm(salon=request.salon)

    return render(request, "staff/form.html", {"form": form, "staff": None})


@salon_member_required
def staff_edit_view(request, pk):
    _require_manager(request)
    staff = get_object_or_404(Staff, pk=pk, salon=request.salon)

    if request.method == "POST":
        form = StaffForm(request.POST, instance=staff, salon=request.salon)
        if form.is_valid():
            form.save()
            messages.success(request, f"{staff.name} updated.")
            return redirect("staff-list")
    else:
        form = StaffForm(instance=staff, salon=request.salon)

    return render(request, "staff/form.html", {"form": form, "staff": staff})


@require_POST
@salon_member_required
def staff_delete_view(request, pk):
    _require_manager(request)
    staff = get_object_or_404(Staff, pk=pk, salon=request.salon)
    staff.delete()
    messages.success(request, f"{staff.name} removed.")
    return redirect("staff-list")


@salon_member_required
def staff_services_view(request, pk):
    _require_manager(request)
    staff = get_object_or_404(Staff, pk=pk, salon=request.salon)

    if request.method == "POST":
        form = StaffServicesForm(request.POST, salon=request.salon)
        if form.is_valid():
            selected = form.cleaned_data["services"]
            StaffService.objects.filter(staff=staff).exclude(service__in=selected).delete()
            existing_service_ids = set(
                StaffService.objects.filter(staff=staff).values_list("service_id", flat=True)
            )
            StaffService.objects.bulk_create(
                [
                    StaffService(salon=request.salon, staff=staff, service=service)
                    for service in selected
                    if service.id not in existing_service_ids
                ]
            )
            messages.success(request, f"Services updated for {staff.name}.")
            return redirect("staff-list")
    else:
        assigned_ids = StaffService.objects.filter(staff=staff).values_list(
            "service_id", flat=True
        )
        form = StaffServicesForm(salon=request.salon, initial={"services": list(assigned_ids)})

    return render(request, "staff/services.html", {"form": form, "staff": staff})
