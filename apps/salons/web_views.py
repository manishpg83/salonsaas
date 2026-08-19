from django.shortcuts import render

from apps.catalog.models import Service
from apps.core.decorators import salon_member_required


@salon_member_required
def dashboard_view(request):
    services = Service.objects.filter(salon=request.salon).select_related("category")
    return render(
        request,
        "salons/dashboard.html",
        {
            "salon": request.salon,
            "membership": request.membership,
            "services": services,
        },
    )
