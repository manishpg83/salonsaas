from apps.salons.models import Membership


def get_active_membership(user):
    """Look up the authenticated user's currently-active salon Membership.

    Imports apps.salons directly rather than via apps.get_model() — this
    module (like apps/core/views.py, which calls it) is only ever imported
    after the app registry is fully populated (via urls.py → views.py), so
    there's no import-time ordering hazard despite apps.core being listed
    before apps.salons in INSTALLED_APPS.
    """
    if not user or not user.is_authenticated:
        return None

    return (
        Membership.objects.filter(user=user, is_current=True)
        .select_related("salon")
        .first()
    )
