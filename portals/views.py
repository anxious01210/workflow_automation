# portals/views.py
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView
from django.core.exceptions import PermissionDenied


class PortalHomeView(LoginRequiredMixin, TemplateView):
    template_name = "portals/home.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm("portals.portal_access"):
            raise PermissionDenied("You do not have portal access.")
        return super().dispatch(request, *args, **kwargs)


class AppointmentsView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "portals.appointments_view"
    template_name = "portals/appointments.html"


class LeaveView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "portals.leave_submit"
    template_name = "portals/leave.html"


class PurchasesView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    permission_required = "portals.purchase_submit"
    template_name = "portals/purchases.html"
