# portals/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

class StudentDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "portals/student_dashboard.html"

class FacultyDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "portals/faculty_dashboard.html"

class StaffDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "portals/staff_dashboard.html"

class GuardianDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "portals/guardian_dashboard.html"

class ExternalDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "portals/external_dashboard.html"
