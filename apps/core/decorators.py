from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .salon_context import get_active_membership


def salon_member_required(view_func):
    """Template-view equivalent of SalonScopedViewSet (see CLAUDE.md §4.2).
    Requires login, then resolves request.membership/request.salon before
    the view runs. Unlike the old DRF viewset, there's no automatic
    queryset filtering here — views must still filter by salon=request.salon
    explicitly."""

    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        request.membership = get_active_membership(request.user)
        request.salon = request.membership.salon if request.membership else None
        if request.salon is None:
            # Every user gets an OWNER Membership at signup (apps.salons
            # signal) — this should be unreachable, but fail safe.
            return redirect("login")
        return view_func(request, *args, **kwargs)

    return wrapper
