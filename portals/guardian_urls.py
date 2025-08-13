# portals/guardian_urls.py
from django.urls import path
from .views import GuardianDashboardView

app_name = "guardian"
urlpatterns = [
    path("", GuardianDashboardView.as_view(), name="dashboard"),
]
