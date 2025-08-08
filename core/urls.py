from django.urls import path
from . import views

app_name = 'core'
urlpatterns = [
    path('builder/<int:workflow_id>/', views.workflow_builder, name='workflow_builder'),
    path('workflow/<int:workflow_id>/test-form/', views.workflow_form_test, name='workflow_form_test'),
    path('workflow/<int:workflow_id>/preview/', views.workflow_preview, name='workflow_preview'),
]
