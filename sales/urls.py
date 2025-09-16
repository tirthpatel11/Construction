from django.urls import path
from . import views
from . import api_views

app_name = 'sales'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('buildings/', views.building_list, name='building_list'),
    path('buildings/create/', views.building_create, name='building_create'),
    path('buildings/<int:building_id>/', views.building_detail, name='building_detail'),
    path('units/', views.unit_list, name='unit_list'),
    path('units/create/', views.unit_create, name='unit_create'),
    path('units/<int:unit_id>/', views.unit_detail, name='unit_detail'),
    path('units/<int:unit_id>/edit/', views.unit_edit, name='unit_edit'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.customer_create, name='customer_create'),
    path('customers/<int:customer_id>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:customer_id>/edit/', views.customer_edit, name='customer_edit'),
    path('bookings/', views.booking_list, name='booking_list'),
    path('bookings/create/', views.booking_create, name='booking_create'),
    path('bookings/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('bookings/<int:booking_id>/edit/', views.booking_edit, name='booking_edit'),
    path('bookings/<int:booking_id>/delete/', views.booking_delete, name='booking_delete'),
    path('payments/create/<int:booking_id>/', views.payment_create, name='payment_create'),
    path('price-lists/', views.price_list_view, name='price_list'),
    path('price-lists/create/', views.price_list_create, name='price_list_create'),
    path('reports/', views.sales_reports, name='sales_reports'),
    # API endpoints
    path('api/buildings/', api_views.get_buildings, name='api_buildings'),
    path('api/wings/', api_views.get_wings, name='api_wings'),
    path('api/units/', api_views.get_units, name='api_units'),
    path('api/customers/', api_views.get_customers, name='api_customers'),
]
