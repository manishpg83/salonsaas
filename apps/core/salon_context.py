from django.apps import apps


def get_active_membership(user):
    """
    Look up the authenticated user's active salon Membership.

    Uses apps.get_model() instead of a direct import: apps.core is built
    before apps.salons (see CLAUDE.md build order), so core can't have a
    hard import-time dependency on a model that doesn't exist yet. By the
    time this function is actually called at runtime, apps.salons (Phase
    1.3) will be installed.
    """
    if not user or not user.is_authenticated:
        return None

    Membership = apps.get_model("salons", "Membership")
    return (
        Membership.objects.filter(user=user, is_active=True)
        .select_related("salon")
        .first()
    )
