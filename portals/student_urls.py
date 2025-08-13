# portals/student_urls.py
from django.urls import path
from .views import StudentDashboardView

app_name = "student"
urlpatterns = [
    path("", StudentDashboardView.as_view(), name="dashboard"),
]
