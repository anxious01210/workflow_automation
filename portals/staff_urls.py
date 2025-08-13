# portals/staff_urls.py
from django.urls import path
from .views import StaffDashboardView

app_name = "staff"
urlpatterns = [
    path("", StaffDashboardView.as_view(), name="dashboard"),
]
