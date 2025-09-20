from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard, name='dashboard'),
    path('create/', views.create_report_request, name='create'),
    path('download/<int:report_id>/', views.download_report, name='download'),
    path('delete/<int:report_id>/', views.delete_report, name='delete'),
]
