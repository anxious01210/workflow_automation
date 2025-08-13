# portals/faculty_urls.py
from django.urls import path
from .views import FacultyDashboardView

app_name = "faculty"
urlpatterns = [
    path("", FacultyDashboardView.as_view(), name="dashboard"),
]
