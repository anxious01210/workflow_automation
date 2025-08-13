# portals/urls.py
from django.urls import path, include
from . import views

app_name = 'portals'

urlpatterns = [
    path("student/", include(("portals.student_urls", "student"), namespace="student")),
    path("faculty/", include(("portals.faculty_urls", "faculty"), namespace="faculty")),
    path("staff/", include(("portals.staff_urls", "staff"), namespace="staff")),
    path("guardian/", include(("portals.guardian_urls", "guardian"), namespace="guardian")),
    path("external/", include(("portals.external_urls", "external"), namespace="external")),
]
