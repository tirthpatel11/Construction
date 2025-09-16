from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('create/', views.create_project, name='create'),
    path('list/', views.project_list, name='list'),
    path('<int:project_id>/', views.project_detail, name='detail'),
    path('<int:project_id>/edit/', views.edit_project, name='edit'),
    path('<int:project_id>/delete/', views.delete_project, name='delete'),
    path('<int:project_id>/analytics/', views.project_analytics, name='analytics'),
    # Expense routes
    path('<int:project_id>/expenses/add/', views.expense_create, name='expense_add'),
    path('<int:project_id>/expenses/<int:expense_id>/edit/', views.expense_edit, name='expense_edit'),
    path('<int:project_id>/expenses/<int:expense_id>/delete/', views.expense_delete, name='expense_delete'),
]