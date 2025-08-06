from django.urls import path
from . import views

app_name = 'core'
urlpatterns = [
    path('builder/<int:workflow_id>/', views.workflow_builder, name='workflow_builder'),
    path('workflow/<int:workflow_id>/preview/', views.workflow_preview, name='workflow_preview'),
]
