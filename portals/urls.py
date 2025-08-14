# portals/urls.py
from django.urls import path
from . import views

app_name = "portals"  # matches project include(namespace="portals")

urlpatterns = [
    path("home/", views.PortalHomeView.as_view(), name="home"),
    path("appointments/", views.AppointmentsView.as_view(), name="appointments"),
    path("leave/", views.LeaveView.as_view(), name="leave"),
    path("purchases/", views.PurchasesView.as_view(), name="purchases"),
]
