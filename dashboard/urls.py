from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home, name='home'),
    path('project-selection/', views.project_selection, name='project_selection'),
    path('analytics-data/', views.analytics_data, name='analytics_data'),
    path('settings/', views.settings_view, name='settings'),
]