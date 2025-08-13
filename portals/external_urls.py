# portals/external_urls.py
from django.urls import path
from .views import ExternalDashboardView

app_name = "external"
urlpatterns = [
    path("", ExternalDashboardView.as_view(), name="dashboard"),
]
